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

// Connector exports
export * from './connectors/RelationshipDefinitions.js';

// Example schemas (optional)
export * as MMORPGSchemas from './schemas/examples/mmorpg-schemas.js';
