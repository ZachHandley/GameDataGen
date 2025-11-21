import { globalContext, GeneratedEntity } from './ContextManager.js';
import { globalRelationships } from '../connectors/RelationshipDefinitions.js';
import { globalRegistry } from './SchemaRegistry.js';
import { GenerationEngine } from './GenerationEngine.js';

/**
 * Tracks which entities are affected by changes to other entities
 */
export interface AffectedEntities {
  direct: GeneratedEntity[]; // Entities that directly reference this one
  indirect: GeneratedEntity[]; // Entities that reference the direct ones
  all: GeneratedEntity[]; // All affected entities (direct + indirect)
}

/**
 * Result of an edit operation
 */
export interface EditResult {
  success: boolean;
  updatedEntity?: GeneratedEntity;
  affectedEntities?: AffectedEntities;
  error?: string;
}

/**
 * Options for regeneration
 */
export interface RegenerationOptions {
  regenerateDirect?: boolean; // Regenerate directly affected entities
  regenerateIndirect?: boolean; // Regenerate indirectly affected entities
  specifications?: Record<string, any>; // Additional specs for regeneration
}

/**
 * System for editing generated content and tracking dependencies
 */
export class EditingSystem {
  private engine: GenerationEngine;

  constructor(engine: GenerationEngine) {
    this.engine = engine;
  }

  /**
   * Edit an existing entity
   */
  async editEntity(
    entityType: string,
    entityId: string,
    updates: Partial<any>,
    options?: {
      validate?: boolean; // Validate against schema (default: true)
      trackAffected?: boolean; // Track affected entities (default: true)
    }
  ): Promise<EditResult> {
    try {
      const entity = globalContext.getEntity(entityType, entityId);
      if (!entity) {
        return {
          success: false,
          error: `Entity "${entityId}" of type "${entityType}" not found`,
        };
      }

      // Merge updates
      const updatedData = { ...entity.data, ...updates };

      // Validate if requested
      if (options?.validate !== false) {
        const schema = globalRegistry.get(entityType);
        if (schema) {
          schema.schema.parse(updatedData);
        }
      }

      // Update the entity
      const updatedEntity: GeneratedEntity = {
        ...entity,
        data: updatedData,
        metadata: {
          ...entity.metadata,
          lastEditedAt: new Date(),
        },
      };

      // Update in context (we need to add an update method to ContextManager)
      globalContext.addEntity(updatedEntity); // This overwrites the existing one

      // Track affected entities
      const affectedEntities =
        options?.trackAffected !== false
          ? this.getAffectedEntities(entityType, entityId)
          : undefined;

      return {
        success: true,
        updatedEntity,
        affectedEntities,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Get all entities affected by changes to a specific entity
   */
  getAffectedEntities(entityType: string, entityId: string): AffectedEntities {
    const direct: GeneratedEntity[] = [];
    const indirect: GeneratedEntity[] = [];

    // Find entities that reference this one
    const allEntities = globalContext.getAllEntities();

    for (const entity of allEntities) {
      if (!entity.relationships) continue;

      // Check if this entity references our target
      for (const [relType, relIds] of Object.entries(entity.relationships)) {
        if (relType === entityType) {
          const ids = Array.isArray(relIds) ? relIds : [relIds];
          if (ids.includes(entityId)) {
            direct.push(entity);
            break;
          }
        }
      }
    }

    // Find entities that reference the direct ones (2 levels deep)
    for (const directEntity of direct) {
      for (const entity of allEntities) {
        if (!entity.relationships) continue;
        if (direct.includes(entity) || indirect.includes(entity)) continue;

        for (const [relType, relIds] of Object.entries(entity.relationships)) {
          if (relType === directEntity.type) {
            const ids = Array.isArray(relIds) ? relIds : [relIds];
            if (ids.includes(directEntity.id)) {
              indirect.push(entity);
              break;
            }
          }
        }
      }
    }

    return {
      direct,
      indirect,
      all: [...direct, ...indirect],
    };
  }

  /**
   * Regenerate entities affected by an edit
   */
  async regenerateAffected(
    affectedEntities: AffectedEntities,
    options: RegenerationOptions = {}
  ): Promise<{
    success: boolean;
    regenerated: GeneratedEntity[];
    errors: Array<{ entityId: string; error: string }>;
  }> {
    const regenerated: GeneratedEntity[] = [];
    const errors: Array<{ entityId: string; error: string }> = [];

    const toRegenerate: GeneratedEntity[] = [];

    if (options.regenerateDirect) {
      toRegenerate.push(...affectedEntities.direct);
    }

    if (options.regenerateIndirect) {
      toRegenerate.push(...affectedEntities.indirect);
    }

    // Regenerate each entity
    for (const entity of toRegenerate) {
      try {
        const result = await this.engine.generate({
          entityType: entity.type,
          count: 1,
          specifications: {
            ...options.specifications,
            id: entity.id, // Keep the same ID
          },
          linkToExisting: this.extractExistingLinks(entity),
        });

        if (result.success && result.entities.length > 0) {
          regenerated.push(result.entities[0]);
        } else {
          errors.push({
            entityId: entity.id,
            error: result.error || 'Unknown error',
          });
        }
      } catch (error) {
        errors.push({
          entityId: entity.id,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    return {
      success: errors.length === 0,
      regenerated,
      errors,
    };
  }

  /**
   * Extract existing links from an entity
   */
  private extractExistingLinks(
    entity: GeneratedEntity
  ): Array<{ entityType: string; entityId: string }> {
    const links: Array<{ entityType: string; entityId: string }> = [];

    if (!entity.relationships) return links;

    for (const [entityType, ids] of Object.entries(entity.relationships)) {
      const idArray = Array.isArray(ids) ? ids : [ids];
      for (const id of idArray) {
        links.push({ entityType, entityId: id });
      }
    }

    return links;
  }

  /**
   * Bulk edit multiple entities
   */
  async bulkEdit(
    edits: Array<{
      entityType: string;
      entityId: string;
      updates: Partial<any>;
    }>,
    options?: {
      validate?: boolean;
      regenerateAffected?: boolean;
      regenerationOptions?: RegenerationOptions;
    }
  ): Promise<{
    success: boolean;
    results: EditResult[];
    regenerated?: GeneratedEntity[];
  }> {
    const results: EditResult[] = [];
    const allAffected = new Set<string>();

    // Perform all edits
    for (const edit of edits) {
      const result = await this.editEntity(
        edit.entityType,
        edit.entityId,
        edit.updates,
        { validate: options?.validate }
      );

      results.push(result);

      // Collect affected entities
      if (result.affectedEntities) {
        for (const entity of result.affectedEntities.all) {
          allAffected.add(`${entity.type}:${entity.id}`);
        }
      }
    }

    // Optionally regenerate affected
    let regenerated: GeneratedEntity[] | undefined;

    if (options?.regenerateAffected && allAffected.size > 0) {
      const affectedEntities: AffectedEntities = {
        direct: [],
        indirect: [],
        all: [],
      };

      for (const key of allAffected) {
        const [type, id] = key.split(':');
        const entity = globalContext.getEntity(type, id);
        if (entity) {
          affectedEntities.all.push(entity);
        }
      }

      const regenResult = await this.regenerateAffected(
        affectedEntities,
        options.regenerationOptions || { regenerateDirect: true }
      );

      regenerated = regenResult.regenerated;
    }

    return {
      success: results.every((r) => r.success),
      results,
      regenerated,
    };
  }

  /**
   * Get dependency chain for an entity (what it depends on)
   */
  getDependencyChain(entityType: string, entityId: string): GeneratedEntity[] {
    const chain: GeneratedEntity[] = [];
    const visited = new Set<string>();

    const traverse = (type: string, id: string) => {
      const key = `${type}:${id}`;
      if (visited.has(key)) return;
      visited.add(key);

      const entity = globalContext.getEntity(type, id);
      if (!entity || !entity.relationships) return;

      for (const [relType, relIds] of Object.entries(entity.relationships)) {
        const ids = Array.isArray(relIds) ? relIds : [relIds];
        for (const relId of ids) {
          const relEntity = globalContext.getEntity(relType, relId);
          if (relEntity) {
            chain.push(relEntity);
            traverse(relType, relId);
          }
        }
      }
    };

    traverse(entityType, entityId);
    return chain;
  }

  /**
   * Validate all relationships in the system
   */
  validateAllRelationships(): {
    valid: boolean;
    brokenLinks: Array<{
      from: GeneratedEntity;
      toType: string;
      toId: string;
      missing: true;
    }>;
  } {
    const brokenLinks: Array<{
      from: GeneratedEntity;
      toType: string;
      toId: string;
      missing: true;
    }> = [];

    const allEntities = globalContext.getAllEntities();

    for (const entity of allEntities) {
      if (!entity.relationships) continue;

      for (const [relType, relIds] of Object.entries(entity.relationships)) {
        const ids = Array.isArray(relIds) ? relIds : [relIds];
        for (const id of ids) {
          const target = globalContext.getEntity(relType, id);
          if (!target) {
            brokenLinks.push({
              from: entity,
              toType: relType,
              toId: id,
              missing: true,
            });
          }
        }
      }
    }

    return {
      valid: brokenLinks.length === 0,
      brokenLinks,
    };
  }
}

// Global editing system
export let globalEditingSystem: EditingSystem;

/**
 * Initialize the global editing system
 */
export function initializeEditingSystem(engine: GenerationEngine): void {
  globalEditingSystem = new EditingSystem(engine);
}
