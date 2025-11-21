import { z } from 'zod';
import {
  SchemaRegistry,
  globalRegistry,
  RegisteredSchema,
} from './core/SchemaRegistry.js';
import {
  ContextManager,
  globalContext,
  WorldContext,
  GeneratedEntity,
} from './core/ContextManager.js';
import {
  RelationshipManager,
  globalRelationships,
  RelationshipConfig,
} from './connectors/RelationshipDefinitions.js';
import {
  GenerationEngine,
  globalEngine,
  GenerationConfig,
  GenerationRequest,
  EditCallback,
} from './core/GenerationEngine.js';
import {
  EditingSystem,
  globalEditingSystem,
  initializeEditingSystem,
  EditResult,
  AffectedEntities,
  RegenerationOptions,
} from './core/EditingSystem.js';

/**
 * Main GameDataGen class - orchestrates all systems
 */
export class GameDataGen {
  public readonly schemas: SchemaRegistry;
  public readonly relationships: RelationshipManager;
  public readonly context: ContextManager;
  public readonly engine: GenerationEngine;
  public readonly editing: EditingSystem;

  constructor(config?: GenerationConfig) {
    this.schemas = globalRegistry;
    this.relationships = globalRelationships;
    this.context = globalContext;
    this.engine = config ? new GenerationEngine(config) : globalEngine;
    this.editing = new EditingSystem(this.engine);

    // Initialize global editing system
    initializeEditingSystem(this.engine);
  }

  // ============================================================
  // Schema Management
  // ============================================================

  /**
   * Register a new entity schema
   */
  registerSchema<T extends z.ZodType>(config: RegisteredSchema<T>): this {
    this.schemas.register(config);
    return this;
  }

  /**
   * Define a relationship between entity types
   */
  defineRelationship(config: RelationshipConfig): this {
    this.relationships.define(config);
    return this;
  }

  // ============================================================
  // World Context
  // ============================================================

  /**
   * Set the world context (lore, races, classes, etc.)
   */
  setWorld(context: WorldContext): this {
    this.context.setWorldContext(context);
    return this;
  }

  /**
   * Update world context
   */
  updateWorld(updates: Partial<WorldContext>): this {
    this.context.updateWorldContext(updates);
    return this;
  }

  /**
   * Get current world context
   */
  getWorld(): WorldContext {
    return this.context.getWorldContext();
  }

  // ============================================================
  // Content Generation
  // ============================================================

  /**
   * Generate content for a specific entity type
   */
  async generate(
    entityType: string,
    count: number,
    options?: {
      specifications?: Record<string, any>;
      linkToExisting?: Array<{ entityType: string; entityId: string }>;
      onEachGenerated?: EditCallback;
    }
  ) {
    const request: GenerationRequest = {
      entityType,
      count,
      specifications: options?.specifications,
      linkToExisting: options?.linkToExisting,
      interactive: !!options?.onEachGenerated,
    };

    return this.engine.generate(request, options?.onEachGenerated);
  }

  /**
   * Generate a complete world (zones, NPCs, quests, items, etc.)
   * Respects dependencies and generates in the correct order
   */
  async generateWorld(
    counts: Record<string, number>,
    options?: {
      onEachGenerated?: (
        entityType: string,
        entity: GeneratedEntity,
        index: number,
        total: number
      ) => Promise<void>;
      specifications?: Record<string, Record<string, any>>;
    }
  ) {
    const results: Record<string, GeneratedEntity[]> = {};
    const errors: Array<{ entityType: string; error: string }> = [];

    // Get generation order
    const orderedSchemas = this.schemas.getGenerationOrder();

    for (const schema of orderedSchemas) {
      const count = counts[schema.name];
      if (!count || count === 0) continue;

      console.log(`Generating ${count} ${schema.name}...`);

      try {
        const result = await this.generate(
          schema.name,
          count,
          {
            specifications: options?.specifications?.[schema.name],
            onEachGenerated: options?.onEachGenerated
              ? async (type, data, index, total) => {
                  const entity: GeneratedEntity = {
                    id: data.id,
                    type,
                    data,
                    relationships: {},
                    metadata: { generatedAt: new Date() },
                  };
                  await options.onEachGenerated!(type, entity, index, total);
                  return data;
                }
              : undefined,
          }
        );

        if (result.success) {
          results[schema.name] = result.entities;
          console.log(`✓ Generated ${result.entities.length} ${schema.name}`);
        } else {
          errors.push({
            entityType: schema.name,
            error: result.error || 'Unknown error',
          });
          console.error(`✗ Failed to generate ${schema.name}: ${result.error}`);
        }
      } catch (error) {
        errors.push({
          entityType: schema.name,
          error: error instanceof Error ? error.message : String(error),
        });
        console.error(`✗ Failed to generate ${schema.name}:`, error);
      }
    }

    return {
      success: errors.length === 0,
      results,
      errors,
    };
  }

  // ============================================================
  // Content Editing
  // ============================================================

  /**
   * Edit an existing entity
   */
  async edit(
    entityType: string,
    entityId: string,
    updates: Partial<any>,
    options?: {
      validate?: boolean;
      trackAffected?: boolean;
    }
  ): Promise<EditResult> {
    return this.editing.editEntity(entityType, entityId, updates, options);
  }

  /**
   * Get entities affected by changes to a specific entity
   */
  getAffected(entityType: string, entityId: string): AffectedEntities {
    return this.editing.getAffectedEntities(entityType, entityId);
  }

  /**
   * Regenerate entities affected by an edit
   */
  async regenerateAffected(
    affectedEntities: AffectedEntities,
    options?: RegenerationOptions
  ) {
    return this.editing.regenerateAffected(affectedEntities, options);
  }

  /**
   * Edit an entity and optionally regenerate affected content
   */
  async editAndRegenerate(
    entityType: string,
    entityId: string,
    updates: Partial<any>,
    options?: {
      validate?: boolean;
      regenerateDirect?: boolean;
      regenerateIndirect?: boolean;
    }
  ) {
    const editResult = await this.edit(entityType, entityId, updates, {
      validate: options?.validate,
      trackAffected: true,
    });

    if (!editResult.success || !editResult.affectedEntities) {
      return editResult;
    }

    const regenResult = await this.regenerateAffected(
      editResult.affectedEntities,
      {
        regenerateDirect: options?.regenerateDirect,
        regenerateIndirect: options?.regenerateIndirect,
      }
    );

    return {
      ...editResult,
      regenerated: regenResult.regenerated,
      regenerationErrors: regenResult.errors,
    };
  }

  // ============================================================
  // Content Retrieval
  // ============================================================

  /**
   * Get a specific entity
   */
  getEntity(entityType: string, entityId: string): GeneratedEntity | undefined {
    return this.context.getEntity(entityType, entityId);
  }

  /**
   * Get all entities of a specific type
   */
  getEntities(entityType: string): GeneratedEntity[] {
    return this.context.getEntitiesByType(entityType);
  }

  /**
   * Get all generated content
   */
  getAllEntities(): GeneratedEntity[] {
    return this.context.getAllEntities();
  }

  /**
   * Get generation statistics
   */
  getStats() {
    return this.context.getStats();
  }

  // ============================================================
  // Data Import/Export
  // ============================================================

  /**
   * Export all data as JSON
   */
  export(): {
    worldContext: WorldContext;
    entities: GeneratedEntity[];
  } {
    return this.context.exportData();
  }

  /**
   * Import data from JSON
   */
  import(data: { worldContext?: WorldContext; entities?: GeneratedEntity[] }): this {
    this.context.importData(data);
    return this;
  }

  /**
   * Save to file
   */
  async saveToFile(filepath: string): Promise<void> {
    const data = this.export();
    const fs = await import('fs/promises');
    await fs.writeFile(filepath, JSON.stringify(data, null, 2));
  }

  /**
   * Load from file
   */
  async loadFromFile(filepath: string): Promise<void> {
    const fs = await import('fs/promises');
    const content = await fs.readFile(filepath, 'utf-8');
    const data = JSON.parse(content);
    this.import(data);
  }

  // ============================================================
  // Validation & Debugging
  // ============================================================

  /**
   * Validate all relationships
   */
  validateRelationships() {
    return this.editing.validateAllRelationships();
  }

  /**
   * Get dependency chain for an entity
   */
  getDependencies(entityType: string, entityId: string): GeneratedEntity[] {
    return this.editing.getDependencyChain(entityType, entityId);
  }

  /**
   * Clear all generated content (keeps schemas and relationships)
   */
  clear(): this {
    this.context.clear();
    return this;
  }

  /**
   * Reset everything (including schemas and relationships)
   */
  reset(): this {
    this.schemas.clear();
    this.relationships.clear();
    this.context.clear();
    return this;
  }
}

// Export a default instance
export const gameDataGen = new GameDataGen();

// Export all types
export * from './core/SchemaRegistry.js';
export * from './core/ContextManager.js';
export * from './connectors/RelationshipDefinitions.js';
export * from './core/GenerationEngine.js';
export * from './core/EditingSystem.js';
