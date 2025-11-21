import {
  Workflow,
  StartEvent,
  StopEvent,
  WorkflowEvent,
  Context,
} from 'llamaindex';
import { createGenerationTools } from './GenerationTools.js';
import { globalRegistry } from '../core/SchemaRegistry.js';
import { globalContext, GeneratedEntity } from '../core/ContextManager.js';
import { globalRelationships } from '../connectors/RelationshipDefinitions.js';

/**
 * Events for the generation workflow
 */
export class GenerationRequestEvent extends WorkflowEvent<{
  entityType: string;
  count: number;
  specifications?: Record<string, any>;
  linkToExisting?: Array<{ entityType: string; entityId: string }>;
}> {}

export class GenerationCompleteEvent extends WorkflowEvent<{
  entities: GeneratedEntity[];
  success: boolean;
  error?: string;
}> {}

export class ContextAnalysisEvent extends WorkflowEvent<{
  entityType: string;
  relevantContext: string;
  dependencies: string[];
}> {}

/**
 * Main generation workflow using LlamaIndex
 * Orchestrates the content generation process with function calling
 */
export class GameContentGenerationWorkflow extends Workflow {
  private tools = createGenerationTools();

  constructor() {
    super();
  }

  /**
   * Step 1: Analyze context and dependencies
   */
  async analyzeContext(
    context: Context,
    ev: StartEvent | GenerationRequestEvent
  ): Promise<ContextAnalysisEvent> {
    const { entityType, specifications } = ev.data;

    // Get schema information
    const schema = globalRegistry.get(entityType);
    if (!schema) {
      throw new Error(`Schema "${entityType}" not found`);
    }

    // Get dependencies
    const dependencies = schema.dependencies || [];

    // Check if dependencies are satisfied
    for (const dep of dependencies) {
      const depEntities = globalContext.getEntitiesByType(dep);
      if (depEntities.length === 0) {
        console.warn(
          `Warning: No entities of type "${dep}" exist yet, but "${entityType}" depends on it`
        );
      }
    }

    // Build relevant context
    const relationships = globalRelationships.getContextualRelationships(entityType);
    const relatedTypes = relationships.map((r) => r.to);

    const relevantContext = globalContext.buildGenerationContext(entityType, {
      includeRelatedTypes: [...dependencies, ...relatedTypes],
      maxEntitiesPerType: 10,
      includeHistory: true,
    });

    return new ContextAnalysisEvent({
      data: {
        entityType,
        relevantContext,
        dependencies,
      },
    });
  }

  /**
   * Step 2: Generate content using LLM
   */
  async generateContent(
    context: Context,
    ev: ContextAnalysisEvent
  ): Promise<GenerationCompleteEvent> {
    const { entityType, relevantContext } = ev.data;
    const request = context.get('request') as GenerationRequestEvent['data'];

    try {
      // Get schema details
      const schema = globalRegistry.get(entityType);
      if (!schema) {
        throw new Error(`Schema "${entityType}" not found`);
      }

      const jsonSchema = globalRegistry.getJsonSchema(entityType);
      const entities: GeneratedEntity[] = [];

      // Generate the requested number of entities
      for (let i = 0; i < request.count; i++) {
        const generatedData = await this.generateSingleEntity(
          entityType,
          jsonSchema,
          relevantContext,
          request.specifications,
          i + 1,
          request.count
        );

        // Create entity record
        const entity: GeneratedEntity = {
          id: generatedData.id || `${entityType}_${Date.now()}_${i}`,
          type: entityType,
          data: generatedData,
          relationships: this.extractRelationships(
            generatedData,
            entityType,
            request.linkToExisting
          ),
          metadata: {
            generatedAt: new Date(),
            index: i,
            totalCount: request.count,
          },
        };

        // Add to context
        globalContext.addEntity(entity);
        entities.push(entity);
      }

      return new GenerationCompleteEvent({
        data: {
          entities,
          success: true,
        },
      });
    } catch (error) {
      return new GenerationCompleteEvent({
        data: {
          entities: [],
          success: false,
          error: error instanceof Error ? error.message : String(error),
        },
      });
    }
  }

  /**
   * Generate a single entity using the LLM
   */
  private async generateSingleEntity(
    entityType: string,
    jsonSchema: any,
    context: string,
    specifications: Record<string, any> = {},
    index: number,
    total: number
  ): Promise<any> {
    // This is where you would call your LLM via LiteLLM
    // For now, this is a placeholder that returns the structure

    const prompt = this.buildGenerationPrompt(
      entityType,
      jsonSchema,
      context,
      specifications,
      index,
      total
    );

    // TODO: Integrate with LiteLLM here
    // const response = await litellm.completion({
    //   model: "gpt-4.5-turbo",
    //   messages: [{ role: "user", content: prompt }],
    //   tools: this.tools,
    // });

    // For now, return a placeholder
    console.log(`Generated ${entityType} ${index}/${total}`);

    return {
      id: `${entityType}_${Date.now()}_${index}`,
      // Add other fields based on schema
      ...specifications,
    };
  }

  /**
   * Build the generation prompt
   */
  private buildGenerationPrompt(
    entityType: string,
    jsonSchema: any,
    context: string,
    specifications: Record<string, any>,
    index: number,
    total: number
  ): string {
    return `You are a creative game content generator for an MMORPG.

${context}

Your task: Generate ${entityType} #${index} of ${total}.

Schema Requirements:
${JSON.stringify(jsonSchema, null, 2)}

${
  Object.keys(specifications).length > 0
    ? `Additional Specifications:\n${JSON.stringify(specifications, null, 2)}`
    : ''
}

Guidelines:
1. Ensure the generated content is thematically consistent with the world lore
2. Make it unique and interesting
3. Ensure all relationships to existing entities are valid
4. Follow the schema structure exactly
5. Be creative but maintain internal consistency

Generate the ${entityType} as a valid JSON object matching the schema:`;
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

    // Get defined relationships for this entity type
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
   * Define workflow steps
   */
  override defineSteps(): void {
    this.addStep(
      {
        inputs: [StartEvent, GenerationRequestEvent],
        outputs: [ContextAnalysisEvent],
      },
      this.analyzeContext.bind(this)
    );

    this.addStep(
      {
        inputs: [ContextAnalysisEvent],
        outputs: [GenerationCompleteEvent, StopEvent],
      },
      this.generateContent.bind(this)
    );
  }
}

/**
 * Helper function to run a generation request
 */
export async function generateGameContent(request: {
  entityType: string;
  count: number;
  specifications?: Record<string, any>;
  linkToExisting?: Array<{ entityType: string; entityId: string }>;
}): Promise<GeneratedEntity[]> {
  const workflow = new GameContentGenerationWorkflow();

  const result = await workflow.run(new GenerationRequestEvent({ data: request }));

  if (!result.data.success) {
    throw new Error(result.data.error || 'Generation failed');
  }

  return result.data.entities;
}
