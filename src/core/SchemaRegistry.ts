import { z } from 'zod';

/**
 * Represents a registered schema with metadata
 */
export interface RegisteredSchema<T extends z.ZodType = z.ZodType> {
  name: string;
  schema: T;
  description?: string;
  dependencies?: string[]; // Other schema names this depends on
  generationPriority?: number; // Lower numbers generate first
}

/**
 * Central registry for user-provided schemas
 * Users register their own Zod schemas for any game entity type
 */
export class SchemaRegistry {
  private schemas: Map<string, RegisteredSchema> = new Map();

  /**
   * Register a new schema
   * @param config Schema configuration
   */
  register<T extends z.ZodType>(config: RegisteredSchema<T>): void {
    if (this.schemas.has(config.name)) {
      throw new Error(`Schema "${config.name}" is already registered`);
    }

    // Validate dependencies exist
    if (config.dependencies) {
      for (const dep of config.dependencies) {
        if (!this.schemas.has(dep)) {
          console.warn(
            `Warning: Schema "${config.name}" depends on "${dep}" which is not yet registered`
          );
        }
      }
    }

    this.schemas.set(config.name, config);
  }

  /**
   * Get a registered schema by name
   */
  get(name: string): RegisteredSchema | undefined {
    return this.schemas.get(name);
  }

  /**
   * Get all registered schemas
   */
  getAll(): RegisteredSchema[] {
    return Array.from(this.schemas.values());
  }

  /**
   * Get schemas in generation order (respecting dependencies and priority)
   */
  getGenerationOrder(): RegisteredSchema[] {
    const schemas = this.getAll();
    const sorted: RegisteredSchema[] = [];
    const visited = new Set<string>();
    const visiting = new Set<string>();

    const visit = (schemaName: string) => {
      if (visited.has(schemaName)) return;
      if (visiting.has(schemaName)) {
        throw new Error(`Circular dependency detected involving "${schemaName}"`);
      }

      const schema = this.schemas.get(schemaName);
      if (!schema) return;

      visiting.add(schemaName);

      // Visit dependencies first
      if (schema.dependencies) {
        for (const dep of schema.dependencies) {
          visit(dep);
        }
      }

      visiting.delete(schemaName);
      visited.add(schemaName);
      sorted.push(schema);
    };

    // Visit all schemas
    for (const schema of schemas) {
      visit(schema.name);
    }

    // Sort by priority within dependency levels
    return sorted.sort((a, b) => {
      const priorityA = a.generationPriority ?? 100;
      const priorityB = b.generationPriority ?? 100;
      return priorityA - priorityB;
    });
  }

  /**
   * Check if a schema is registered
   */
  has(name: string): boolean {
    return this.schemas.has(name);
  }

  /**
   * Unregister a schema
   */
  unregister(name: string): boolean {
    return this.schemas.delete(name);
  }

  /**
   * Clear all registered schemas
   */
  clear(): void {
    this.schemas.clear();
  }

  /**
   * Get JSON Schema representation of a registered schema
   * Useful for passing to LLMs
   */
  getJsonSchema(name: string): any {
    const registered = this.schemas.get(name);
    if (!registered) {
      throw new Error(`Schema "${name}" not found`);
    }

    // Convert Zod schema to JSON Schema
    // Note: This is a simplified version - you may want to use a library
    // like zod-to-json-schema for more complete conversion
    return this.zodToJsonSchema(registered.schema);
  }

  private zodToJsonSchema(schema: z.ZodType): any {
    // This is a basic implementation
    // For production, use a library like zod-to-json-schema
    const def = (schema as any)._def;

    if (schema instanceof z.ZodObject) {
      const shape = schema.shape;
      const properties: any = {};
      const required: string[] = [];

      for (const [key, value] of Object.entries(shape)) {
        properties[key] = this.zodToJsonSchema(value as z.ZodType);
        if (!(value as z.ZodType).isOptional()) {
          required.push(key);
        }
      }

      return {
        type: 'object',
        properties,
        required: required.length > 0 ? required : undefined,
      };
    }

    if (schema instanceof z.ZodString) {
      return { type: 'string' };
    }

    if (schema instanceof z.ZodNumber) {
      return { type: 'number' };
    }

    if (schema instanceof z.ZodBoolean) {
      return { type: 'boolean' };
    }

    if (schema instanceof z.ZodArray) {
      return {
        type: 'array',
        items: this.zodToJsonSchema((schema as any)._def.type),
      };
    }

    if (schema instanceof z.ZodEnum) {
      return {
        type: 'string',
        enum: (schema as any)._def.values,
      };
    }

    if (schema instanceof z.ZodOptional) {
      return this.zodToJsonSchema((schema as any)._def.innerType);
    }

    if (schema instanceof z.ZodNullable) {
      const innerSchema = this.zodToJsonSchema((schema as any)._def.innerType);
      return {
        ...innerSchema,
        nullable: true,
      };
    }

    // Default fallback
    return { type: 'object' };
  }
}

// Global registry instance
export const globalRegistry = new SchemaRegistry();
