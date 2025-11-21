/**
 * Defines how different entity types relate to each other
 * Users define connectors between their schemas
 */

export type RelationshipType =
  | 'one-to-one'
  | 'one-to-many'
  | 'many-to-one'
  | 'many-to-many';

export interface RelationshipConfig {
  from: string; // Schema name
  to: string; // Schema name
  type: RelationshipType;
  fieldName: string; // Field in 'from' that references 'to'
  description?: string;
  required?: boolean; // Is this relationship required?
  contextual?: boolean; // Should context from 'to' be included when generating 'from'?
}

/**
 * Manages relationships between schemas
 */
export class RelationshipManager {
  private relationships: Map<string, RelationshipConfig[]> = new Map();

  /**
   * Define a relationship between two schemas
   */
  define(config: RelationshipConfig): void {
    const key = config.from;
    const existing = this.relationships.get(key) || [];
    existing.push(config);
    this.relationships.set(key, existing);
  }

  /**
   * Get all relationships for a schema
   */
  getRelationships(schemaName: string): RelationshipConfig[] {
    return this.relationships.get(schemaName) || [];
  }

  /**
   * Get relationships where the schema is the target
   */
  getReverseRelationships(schemaName: string): RelationshipConfig[] {
    const result: RelationshipConfig[] = [];
    for (const [, configs] of this.relationships.entries()) {
      for (const config of configs) {
        if (config.to === schemaName) {
          result.push(config);
        }
      }
    }
    return result;
  }

  /**
   * Get all relationships that require context from other entities
   */
  getContextualRelationships(schemaName: string): RelationshipConfig[] {
    return this.getRelationships(schemaName).filter((r) => r.contextual);
  }

  /**
   * Check if a relationship exists
   */
  hasRelationship(from: string, to: string): boolean {
    const relationships = this.relationships.get(from) || [];
    return relationships.some((r) => r.to === to);
  }

  /**
   * Get all unique schema names involved in relationships
   */
  getAllSchemaNames(): Set<string> {
    const names = new Set<string>();
    for (const [from, configs] of this.relationships.entries()) {
      names.add(from);
      for (const config of configs) {
        names.add(config.to);
      }
    }
    return names;
  }

  /**
   * Clear all relationships
   */
  clear(): void {
    this.relationships.clear();
  }
}

// Global relationship manager instance
export const globalRelationships = new RelationshipManager();
