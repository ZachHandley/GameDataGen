import { FunctionTool } from 'llamaindex';
import { globalRegistry } from '../core/SchemaRegistry.js';
import { globalContext } from '../core/ContextManager.js';
import { globalRelationships } from '../connectors/RelationshipDefinitions.js';

/**
 * Tool definitions for the LLM to call during content generation
 */

export interface GenerateContentParams {
  entityType: string;
  count: number;
  specifications?: Record<string, any>;
  linkToExisting?: {
    entityType: string;
    entityId: string;
  }[];
}

export interface GetContextParams {
  entityType?: string;
  includeRelatedTypes?: string[];
}

export interface ListSchemasParams {
  includeDetails?: boolean;
}

/**
 * Create generation tools for the workflow
 */
export function createGenerationTools() {
  /**
   * Tool: List available schemas
   */
  const listSchemasToolcreateGenerationTools = FunctionTool.from<ListSchemasParams>(
    async ({ includeDetails = false }) => {
      const schemas = globalRegistry.getAll();

      if (!includeDetails) {
        return schemas.map((s) => ({
          name: s.name,
          description: s.description,
        }));
      }

      return schemas.map((s) => ({
        name: s.name,
        description: s.description,
        dependencies: s.dependencies,
        generationPriority: s.generationPriority,
        jsonSchema: globalRegistry.getJsonSchema(s.name),
      }));
    },
    {
      name: 'list_schemas',
      description:
        'List all available entity schemas that can be generated. Use this to understand what types of content can be created.',
      parameters: {
        type: 'object',
        properties: {
          includeDetails: {
            type: 'boolean',
            description:
              'Whether to include full schema details including JSON schemas',
          },
        },
      },
    }
  );

  /**
   * Tool: Get world context
   */
  const getContextTool = FunctionTool.from<GetContextParams>(
    async ({ entityType, includeRelatedTypes = [] }) => {
      const worldContext = globalContext.getWorldContext();
      const relationships = entityType
        ? globalRelationships.getContextualRelationships(entityType)
        : [];

      const relatedTypes = [
        ...includeRelatedTypes,
        ...relationships.map((r) => r.to),
      ];

      const contextString = globalContext.buildGenerationContext(
        entityType || 'general',
        {
          includeRelatedTypes: relatedTypes,
          maxEntitiesPerType: 5,
          includeHistory: true,
        }
      );

      return {
        worldContext,
        contextString,
        relationships: relationships.map((r) => ({
          to: r.to,
          type: r.type,
          fieldName: r.fieldName,
        })),
        stats: globalContext.getStats(),
      };
    },
    {
      name: 'get_context',
      description:
        'Get the current world context, lore, and information about existing generated entities. Use this before generating new content to ensure thematic consistency.',
      parameters: {
        type: 'object',
        properties: {
          entityType: {
            type: 'string',
            description: 'The entity type to get context for (optional)',
          },
          includeRelatedTypes: {
            type: 'array',
            items: { type: 'string' },
            description:
              'Additional entity types to include in context (optional)',
          },
        },
      },
    }
  );

  /**
   * Tool: Get schema details
   */
  const getSchemaTool = FunctionTool.from<{ schemaName: string }>(
    async ({ schemaName }) => {
      const schema = globalRegistry.get(schemaName);
      if (!schema) {
        throw new Error(`Schema "${schemaName}" not found`);
      }

      const relationships = globalRelationships.getRelationships(schemaName);
      const jsonSchema = globalRegistry.getJsonSchema(schemaName);

      return {
        name: schema.name,
        description: schema.description,
        dependencies: schema.dependencies,
        relationships: relationships.map((r) => ({
          to: r.to,
          type: r.type,
          fieldName: r.fieldName,
          required: r.required,
          description: r.description,
        })),
        jsonSchema,
      };
    },
    {
      name: 'get_schema',
      description:
        'Get detailed information about a specific schema including its structure, relationships, and requirements.',
      parameters: {
        type: 'object',
        properties: {
          schemaName: {
            type: 'string',
            description: 'The name of the schema to retrieve',
          },
        },
        required: ['schemaName'],
      },
    }
  );

  /**
   * Tool: Get existing entities
   */
  const getEntitiesTool = FunctionTool.from<{
    entityType: string;
    limit?: number;
  }>(
    async ({ entityType, limit = 10 }) => {
      const entities = globalContext.getEntitiesByType(entityType);
      return entities.slice(0, limit).map((e) => ({
        id: e.id,
        type: e.type,
        data: e.data,
        relationships: e.relationships,
      }));
    },
    {
      name: 'get_entities',
      description:
        'Retrieve existing generated entities of a specific type. Use this to reference existing content when creating related entities.',
      parameters: {
        type: 'object',
        properties: {
          entityType: {
            type: 'string',
            description: 'The type of entities to retrieve',
          },
          limit: {
            type: 'number',
            description: 'Maximum number of entities to return (default: 10)',
          },
        },
        required: ['entityType'],
      },
    }
  );

  /**
   * Tool: Record generated content
   * This is called by the generation engine after content is generated
   */
  const recordEntityTool = FunctionTool.from<{
    entityType: string;
    entityId: string;
    data: any;
    relationships?: Record<string, string | string[]>;
    metadata?: any;
  }>(
    async ({ entityType, entityId, data, relationships, metadata }) => {
      globalContext.addEntity({
        id: entityId,
        type: entityType,
        data,
        relationships,
        metadata: {
          ...metadata,
          generatedAt: new Date(),
        },
      });

      return {
        success: true,
        entityId,
        entityType,
      };
    },
    {
      name: 'record_entity',
      description:
        'Record a generated entity in the context. This is typically called by the generation engine after creating content.',
      parameters: {
        type: 'object',
        properties: {
          entityType: {
            type: 'string',
            description: 'The type of entity being recorded',
          },
          entityId: {
            type: 'string',
            description: 'Unique identifier for the entity',
          },
          data: {
            type: 'object',
            description: 'The generated entity data',
          },
          relationships: {
            type: 'object',
            description: 'Related entity IDs by type',
          },
          metadata: {
            type: 'object',
            description: 'Additional metadata about the generation',
          },
        },
        required: ['entityType', 'entityId', 'data'],
      },
    }
  );

  return [
    listSchemasToolcreateGenerationTools,
    getContextTool,
    getSchemaTool,
    getEntitiesTool,
    recordEntityTool,
  ];
}
