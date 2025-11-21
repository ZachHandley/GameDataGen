/**
 * Manages world context, lore, and generated content
 * Provides context to the LLM during generation
 */

export interface WorldContext {
  name?: string;
  description?: string;
  lore?: string;
  theme?: string;
  setting?: string;
  races?: any[];
  classes?: any[];
  professions?: any[];
  factions?: any[];
  [key: string]: any; // User can add any custom context
}

export interface GeneratedEntity {
  id: string;
  type: string; // Schema name
  data: any; // The actual generated data
  relationships?: {
    [key: string]: string | string[]; // Related entity IDs
  };
  metadata?: {
    generatedAt: Date;
    tokens?: number;
    model?: string;
    [key: string]: any;
  };
}

/**
 * Manages the context for content generation
 */
export class ContextManager {
  private worldContext: WorldContext = {};
  private generatedEntities: Map<string, Map<string, GeneratedEntity>> = new Map();
  private generationHistory: GeneratedEntity[] = [];

  /**
   * Set the world context
   */
  setWorldContext(context: WorldContext): void {
    this.worldContext = { ...this.worldContext, ...context };
  }

  /**
   * Get the world context
   */
  getWorldContext(): WorldContext {
    return { ...this.worldContext };
  }

  /**
   * Update specific world context fields
   */
  updateWorldContext(updates: Partial<WorldContext>): void {
    this.worldContext = { ...this.worldContext, ...updates };
  }

  /**
   * Add a generated entity
   */
  addEntity(entity: GeneratedEntity): void {
    if (!this.generatedEntities.has(entity.type)) {
      this.generatedEntities.set(entity.type, new Map());
    }

    const typeMap = this.generatedEntities.get(entity.type)!;
    typeMap.set(entity.id, entity);
    this.generationHistory.push(entity);
  }

  /**
   * Get a generated entity by type and ID
   */
  getEntity(type: string, id: string): GeneratedEntity | undefined {
    return this.generatedEntities.get(type)?.get(id);
  }

  /**
   * Get all entities of a specific type
   */
  getEntitiesByType(type: string): GeneratedEntity[] {
    const typeMap = this.generatedEntities.get(type);
    if (!typeMap) return [];
    return Array.from(typeMap.values());
  }

  /**
   * Get all generated entities
   */
  getAllEntities(): GeneratedEntity[] {
    const result: GeneratedEntity[] = [];
    for (const typeMap of this.generatedEntities.values()) {
      result.push(...Array.from(typeMap.values()));
    }
    return result;
  }

  /**
   * Get generation history (in chronological order)
   */
  getHistory(): GeneratedEntity[] {
    return [...this.generationHistory];
  }

  /**
   * Get related entities for a given entity
   */
  getRelatedEntities(entity: GeneratedEntity): GeneratedEntity[] {
    const related: GeneratedEntity[] = [];

    if (!entity.relationships) return related;

    for (const [type, ids] of Object.entries(entity.relationships)) {
      const idArray = Array.isArray(ids) ? ids : [ids];
      for (const id of idArray) {
        const relatedEntity = this.getEntity(type, id);
        if (relatedEntity) {
          related.push(relatedEntity);
        }
      }
    }

    return related;
  }

  /**
   * Build context for generating a new entity of a specific type
   * This includes world lore and relevant existing entities
   */
  buildGenerationContext(
    schemaName: string,
    options?: {
      includeRelatedTypes?: string[];
      maxEntitiesPerType?: number;
      includeHistory?: boolean;
    }
  ): string {
    const parts: string[] = [];

    // Add world context
    parts.push('=== WORLD CONTEXT ===');
    if (this.worldContext.name) {
      parts.push(`World Name: ${this.worldContext.name}`);
    }
    if (this.worldContext.description) {
      parts.push(`Description: ${this.worldContext.description}`);
    }
    if (this.worldContext.lore) {
      parts.push(`Lore: ${this.worldContext.lore}`);
    }
    if (this.worldContext.theme) {
      parts.push(`Theme: ${this.worldContext.theme}`);
    }

    // Add custom context
    const standardKeys = ['name', 'description', 'lore', 'theme', 'setting'];
    for (const [key, value] of Object.entries(this.worldContext)) {
      if (!standardKeys.includes(key)) {
        parts.push(`${key}: ${JSON.stringify(value, null, 2)}`);
      }
    }

    // Add existing entities for context
    const relatedTypes = options?.includeRelatedTypes || [];
    const maxPerType = options?.maxEntitiesPerType ?? 5;

    if (relatedTypes.length > 0) {
      parts.push('\n=== EXISTING ENTITIES ===');
      for (const type of relatedTypes) {
        const entities = this.getEntitiesByType(type).slice(0, maxPerType);
        if (entities.length > 0) {
          parts.push(`\n${type}:`);
          for (const entity of entities) {
            parts.push(JSON.stringify(entity.data, null, 2));
          }
        }
      }
    }

    // Add recent generation history
    if (options?.includeHistory) {
      const recentHistory = this.generationHistory.slice(-10);
      if (recentHistory.length > 0) {
        parts.push('\n=== RECENT GENERATIONS ===');
        for (const entity of recentHistory) {
          parts.push(`${entity.type}: ${entity.id}`);
        }
      }
    }

    return parts.join('\n');
  }

  /**
   * Export all data as JSON
   */
  exportData(): {
    worldContext: WorldContext;
    entities: GeneratedEntity[];
  } {
    return {
      worldContext: this.getWorldContext(),
      entities: this.getAllEntities(),
    };
  }

  /**
   * Import data from JSON
   */
  importData(data: { worldContext?: WorldContext; entities?: GeneratedEntity[] }): void {
    if (data.worldContext) {
      this.setWorldContext(data.worldContext);
    }

    if (data.entities) {
      for (const entity of data.entities) {
        this.addEntity(entity);
      }
    }
  }

  /**
   * Clear all data
   */
  clear(): void {
    this.worldContext = {};
    this.generatedEntities.clear();
    this.generationHistory = [];
  }

  /**
   * Get statistics about generated content
   */
  getStats(): {
    totalEntities: number;
    entitiesByType: Record<string, number>;
    totalTokens?: number;
  } {
    const stats: any = {
      totalEntities: this.generationHistory.length,
      entitiesByType: {},
    };

    let totalTokens = 0;

    for (const [type, typeMap] of this.generatedEntities.entries()) {
      stats.entitiesByType[type] = typeMap.size;

      for (const entity of typeMap.values()) {
        if (entity.metadata?.tokens) {
          totalTokens += entity.metadata.tokens;
        }
      }
    }

    if (totalTokens > 0) {
      stats.totalTokens = totalTokens;
    }

    return stats;
  }
}

// Global context manager instance
export const globalContext = new ContextManager();
