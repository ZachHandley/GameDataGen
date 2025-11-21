import { OpenAI } from '@llamaindex/openai';
import { z } from 'zod';
import { globalRegistry } from './SchemaRegistry.js';
import { globalContext, GeneratedEntity } from './ContextManager.js';
import { globalRelationships } from '../connectors/RelationshipDefinitions.js';

/**
 * Configuration for the generation engine
 */
export interface GenerationConfig {
  model?: string;
  temperature?: number;
  apiKey?: string;
}

/**
 * Request to generate content
 */
export interface GenerationRequest {
  entityType: string;
  count: number;
  specifications?: Record<string, any>;
  linkToExisting?: Array<{ entityType: string; entityId: string }>;
  interactive?: boolean; // Allow editing during generation
}

/**
 * Result of a generation
 */
export interface GenerationResult {
  entities: GeneratedEntity[];
  success: boolean;
  error?: string;
  tokensUsed?: number;
}

/**
 * Callback for interactive editing
 */
export type EditCallback = (
  entityType: string,
  generatedData: any,
  index: number,
  total: number
) => Promise<any | null>; // Return edited data or null to regenerate

/**
 * Main generation engine using LlamaIndex + OpenAI
 */
export class GenerationEngine {
  private llm: OpenAI;
  private config: GenerationConfig;

  constructor(config: GenerationConfig = {}) {
    this.config = {
      model: config.model || 'gpt-4o-mini',
      temperature: config.temperature ?? 0.8,
      apiKey: config.apiKey || process.env.OPENAI_API_KEY,
    };

    this.llm = new OpenAI({
      model: this.config.model,
      temperature: this.config.temperature,
      apiKey: this.config.apiKey,
    });
  }

  /**
   * Generate content based on request
   */
  async generate(
    request: GenerationRequest,
    editCallback?: EditCallback
  ): Promise<GenerationResult> {
    try {
      // Validate schema exists
      const schema = globalRegistry.get(request.entityType);
      if (!schema) {
        throw new Error(`Schema "${request.entityType}" not found`);
      }

      // Check dependencies
      await this.validateDependencies(request.entityType);

      const entities: GeneratedEntity[] = [];
      let totalTokens = 0;

      // Generate each entity
      for (let i = 0; i < request.count; i++) {
        let generatedData = await this.generateSingleEntity(
          request.entityType,
          schema.schema,
          request.specifications,
          i + 1,
          request.count
        );

        // Interactive editing
        if (editCallback) {
          const edited = await editCallback(
            request.entityType,
            generatedData,
            i + 1,
            request.count
          );

          if (edited === null) {
            // Regenerate
            i--;
            continue;
          } else if (edited !== undefined) {
            generatedData = edited;
          }
        }

        // Validate against schema
        const validated = schema.schema.parse(generatedData);

        // Create entity
        const entity: GeneratedEntity = {
          id: validated.id || `${request.entityType}_${Date.now()}_${i}`,
          type: request.entityType,
          data: validated,
          relationships: this.extractRelationships(
            validated,
            request.entityType,
            request.linkToExisting
          ),
          metadata: {
            generatedAt: new Date(),
            model: this.config.model,
            index: i,
            totalCount: request.count,
          },
        };

        // Add to context
        globalContext.addEntity(entity);
        entities.push(entity);
      }

      return {
        entities,
        success: true,
        tokensUsed: totalTokens,
      };
    } catch (error) {
      return {
        entities: [],
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Generate a single entity
   */
  private async generateSingleEntity(
    entityType: string,
    zodSchema: z.ZodType,
    specifications: Record<string, any> = {},
    index: number,
    total: number
  ): Promise<any> {
    // Build context
    const context = this.buildContext(entityType);

    // Get JSON schema
    const jsonSchema = globalRegistry.getJsonSchema(entityType);

    // Build prompt
    const prompt = this.buildPrompt(
      entityType,
      jsonSchema,
      context,
      specifications,
      index,
      total
    );

    // Call LLM
    const response = await this.llm.complete({
      prompt,
    });

    // Parse JSON response
    const text = response.text;
    const jsonMatch = text.match(/\{[\s\S]*\}/);

    if (!jsonMatch) {
      throw new Error('LLM did not return valid JSON');
    }

    return JSON.parse(jsonMatch[0]);
  }

  /**
   * Build generation context
   */
  private buildContext(entityType: string): string {
    const relationships = globalRelationships.getContextualRelationships(entityType);
    const relatedTypes = relationships.map((r) => r.to);

    const schema = globalRegistry.get(entityType);
    const dependencies = schema?.dependencies || [];

    return globalContext.buildGenerationContext(entityType, {
      includeRelatedTypes: [...dependencies, ...relatedTypes],
      maxEntitiesPerType: 5,
      includeHistory: true,
    });
  }

  /**
   * Build generation prompt
   */
  private buildPrompt(
    entityType: string,
    jsonSchema: any,
    context: string,
    specifications: Record<string, any>,
    index: number,
    total: number
  ): string {
    return `You are a creative game content generator for an MMORPG.

${context}

TASK: Generate ${entityType} #${index} of ${total}.

SCHEMA REQUIREMENTS:
${JSON.stringify(jsonSchema, null, 2)}

${
  Object.keys(specifications).length > 0
    ? `ADDITIONAL SPECIFICATIONS:\n${JSON.stringify(specifications, null, 2)}`
    : ''
}

GUIDELINES:
1. Ensure thematic consistency with the world lore and existing content
2. Make it unique and interesting - avoid generic or repetitive content
3. Ensure all relationships to existing entities are valid references
4. Follow the schema structure exactly
5. Be creative but maintain internal consistency
6. Include an "id" field with a unique identifier

Generate the ${entityType} as a valid JSON object matching the schema. Return ONLY the JSON object, no additional text:`;
  }

  /**
   * Extract relationships from generated data
   */
  private extractRelationships(
    data: any,
    entityType: string,
    linkToExisting?: Array<{ entityType: string; entityId: string }>
  ): Record<string, string | string[]> {
    const relationships: Record<string, string | string[]> = {};

    // Get defined relationships
    const definedRelationships = globalRelationships.getRelationships(entityType);

    for (const rel of definedRelationships) {
      const fieldValue = data[rel.fieldName];
      if (fieldValue) {
        relationships[rel.to] = fieldValue;
      }
    }

    // Add explicit links
    if (linkToExisting) {
      for (const link of linkToExisting) {
        if (!relationships[link.entityType]) {
          relationships[link.entityType] = link.entityId;
        } else if (Array.isArray(relationships[link.entityType])) {
          (relationships[link.entityType] as string[]).push(link.entityId);
        } else {
          relationships[link.entityType] = [
            relationships[link.entityType] as string,
            link.entityId,
          ];
        }
      }
    }

    return relationships;
  }

  /**
   * Validate dependencies are satisfied
   */
  private async validateDependencies(entityType: string): Promise<void> {
    const schema = globalRegistry.get(entityType);
    if (!schema?.dependencies) return;

    for (const dep of schema.dependencies) {
      const depEntities = globalContext.getEntitiesByType(dep);
      if (depEntities.length === 0) {
        console.warn(
          `Warning: No entities of type "${dep}" exist yet, but "${entityType}" depends on it`
        );
      }
    }
  }

  /**
   * Update LLM configuration
   */
  updateConfig(config: Partial<GenerationConfig>): void {
    this.config = { ...this.config, ...config };

    this.llm = new OpenAI({
      model: this.config.model,
      temperature: this.config.temperature,
      apiKey: this.config.apiKey,
    });
  }
}

// Global generation engine
export const globalEngine = new GenerationEngine();
