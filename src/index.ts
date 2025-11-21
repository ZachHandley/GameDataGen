/**
 * GameDataGen - AI-powered game content generation framework
 *
 * Main entry point for the library
 */

export { GameDataGen, gameDataGen } from './GameDataGen.js';

// Core exports
export * from './core/SchemaRegistry.js';
export * from './core/ContextManager.js';
export * from './core/GenerationEngine.js';
export * from './core/EditingSystem.js';
export * from './core/KnowledgeGraph.js';
export * from './core/LevelingSystem.js';
export * from './core/SpatialSystem.js';

// Connector exports
export * from './connectors/RelationshipDefinitions.js';

// Utilities
export * from './utils/IconifyService.js';

// Example schemas (optional)
export * as MMORPGSchemas from './schemas/examples/mmorpg-schemas.js';
export * as EnhancedMMORPGSchemas from './schemas/examples/enhanced-mmorpg-schemas.js';
export * as EventSchemas from './schemas/examples/events-and-random-schemas.js';
