/**
 * LiteLLM integration for calling various LLM providers
 */

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant' | 'function';
  content: string;
  name?: string;
}

export interface LLMTool {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: any;
  };
}

export interface LLMCompletionRequest {
  model: string;
  messages: LLMMessage[];
  temperature?: number;
  maxTokens?: number;
  tools?: LLMTool[];
  toolChoice?: 'auto' | 'required' | { type: 'function'; function: { name: string } };
  responseFormat?: { type: 'json_object' };
}

export interface LLMCompletionResponse {
  id: string;
  model: string;
  choices: Array<{
    message: {
      role: string;
      content: string | null;
      toolCalls?: Array<{
        id: string;
        type: 'function';
        function: {
          name: string;
          arguments: string;
        };
      }>;
    };
    finishReason: string;
  }>;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

/**
 * LiteLLM client wrapper
 */
export class LiteLLMClient {
  private apiKey: string;
  private baseUrl: string;
  private defaultModel: string;

  constructor(options?: {
    apiKey?: string;
    baseUrl?: string;
    defaultModel?: string;
  }) {
    this.apiKey = options?.apiKey || process.env.OPENAI_API_KEY || '';
    this.baseUrl = options?.baseUrl || 'https://api.openai.com/v1';
    this.defaultModel = options?.defaultModel || 'gpt-4o-mini';
  }

  /**
   * Call the LLM with completion request
   */
  async completion(request: LLMCompletionRequest): Promise<LLMCompletionResponse> {
    const url = `${this.baseUrl}/chat/completions`;

    const body: any = {
      model: request.model || this.defaultModel,
      messages: request.messages,
      temperature: request.temperature ?? 0.7,
    };

    if (request.maxTokens) {
      body.max_tokens = request.maxTokens;
    }

    if (request.tools) {
      body.tools = request.tools;
    }

    if (request.toolChoice) {
      body.tool_choice = request.toolChoice;
    }

    if (request.responseFormat) {
      body.response_format = request.responseFormat;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`LLM API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return data as LLMCompletionResponse;
  }

  /**
   * Generate JSON content based on a schema
   */
  async generateJSON<T = any>(options: {
    prompt: string;
    schema: any;
    systemPrompt?: string;
    model?: string;
    temperature?: number;
  }): Promise<T> {
    const messages: LLMMessage[] = [];

    if (options.systemPrompt) {
      messages.push({
        role: 'system',
        content: options.systemPrompt,
      });
    }

    messages.push({
      role: 'user',
      content: `${options.prompt}\n\nGenerate a valid JSON object matching this schema:\n${JSON.stringify(
        options.schema,
        null,
        2
      )}`,
    });

    const response = await this.completion({
      model: options.model || this.defaultModel,
      messages,
      temperature: options.temperature ?? 0.7,
      responseFormat: { type: 'json_object' },
    });

    const content = response.choices[0]?.message?.content;
    if (!content) {
      throw new Error('No content generated');
    }

    try {
      return JSON.parse(content) as T;
    } catch (error) {
      throw new Error(`Failed to parse generated JSON: ${error}`);
    }
  }

  /**
   * Generate multiple items in batch
   */
  async generateBatch<T = any>(options: {
    prompts: string[];
    schema: any;
    systemPrompt?: string;
    model?: string;
    temperature?: number;
    parallel?: boolean;
  }): Promise<T[]> {
    if (options.parallel) {
      const promises = options.prompts.map((prompt) =>
        this.generateJSON<T>({
          prompt,
          schema: options.schema,
          systemPrompt: options.systemPrompt,
          model: options.model,
          temperature: options.temperature,
        })
      );
      return Promise.all(promises);
    } else {
      const results: T[] = [];
      for (const prompt of options.prompts) {
        const result = await this.generateJSON<T>({
          prompt,
          schema: options.schema,
          systemPrompt: options.systemPrompt,
          model: options.model,
          temperature: options.temperature,
        });
        results.push(result);
      }
      return results;
    }
  }

  /**
   * Stream completion (for real-time generation)
   */
  async *streamCompletion(
    request: LLMCompletionRequest
  ): AsyncGenerator<string, void, unknown> {
    const url = `${this.baseUrl}/chat/completions`;

    const body: any = {
      model: request.model || this.defaultModel,
      messages: request.messages,
      temperature: request.temperature ?? 0.7,
      stream: true,
    };

    if (request.maxTokens) {
      body.max_tokens = request.maxTokens;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`LLM API error: ${response.status} - ${error}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices[0]?.delta?.content;
              if (content) {
                yield content;
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}

// Global LLM client instance
export const globalLLM = new LiteLLMClient();

/**
 * Configure the global LLM client
 */
export function configureLLM(options: {
  apiKey?: string;
  baseUrl?: string;
  defaultModel?: string;
}): void {
  Object.assign(globalLLM, options);
}
