# 🎮 GameDataGen

**AI-powered game content generation framework for MMORPGs and beyond**

Generate entire game worlds with NPCs, quests, items, enemies, and more - all thematically consistent and interconnected. Built with TypeScript, Zod, and LlamaIndex.

---

## ✨ Features

- 🧩 **Schema-driven** - Define your game entities using Zod schemas
- 🔗 **Relationship tracking** - Entities automatically reference each other
- 🌍 **World context** - Maintain lore consistency across all generated content
- ✏️ **Interactive editing** - Modify content during or after generation
- 🔄 **Smart regeneration** - Automatically regenerate affected content when you edit
- 📦 **Dependency management** - Generate content in the correct order
- 🎯 **Type-safe** - Full TypeScript support with Zod validation
- 💾 **Import/Export** - Save and load your entire world as JSON

---

## 🚀 Quick Start

### Installation

```bash
npm install
```

### Set up your OpenAI API key

```bash
export OPENAI_API_KEY="your-key-here"
```

### Basic Usage

```typescript
import { GameDataGen } from './src/GameDataGen.js';
import { z } from 'zod';

// 1. Initialize
const gen = new GameDataGen({
  model: 'gpt-4o-mini',
  temperature: 0.8,
});

// 2. Define your schema
const NPCSchema = z.object({
  id: z.string(),
  name: z.string(),
  personality: z.string(),
  dialogue: z.array(z.string()),
});

// 3. Register it
gen.registerSchema({
  name: 'NPC',
  schema: NPCSchema,
  description: 'Non-player characters',
});

// 4. Set world context
gen.setWorld({
  name: 'My Fantasy World',
  lore: 'A realm of magic and mystery...',
  theme: 'High Fantasy',
});

// 5. Generate!
const result = await gen.generate('NPC', 5);

console.log(result.entities); // Your generated NPCs!
```

---

## 📚 Core Concepts

### 1. Schemas

Define your game entities using Zod schemas. The system supports any structure you want:

```typescript
const QuestSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  questGiver: z.string(), // NPC ID
  objectives: z.array(z.object({
    type: z.enum(['kill', 'collect', 'talk']),
    target: z.string(),
    quantity: z.number(),
  })),
  rewards: z.object({
    experience: z.number(),
    gold: z.number(),
    items: z.array(z.string()),
  }),
});

gen.registerSchema({
  name: 'Quest',
  schema: QuestSchema,
  description: 'Quests and storylines',
  dependencies: ['NPC', 'Item', 'Enemy'], // Generate these first!
  generationPriority: 6, // Lower = earlier
});
```

### 2. Relationships

Define how entities connect:

```typescript
gen.defineRelationship({
  from: 'Quest',
  to: 'NPC',
  type: 'many-to-one',
  fieldName: 'questGiver',
  contextual: true, // Include NPC data when generating quests
  required: true,
});
```

### 3. World Context

Provide lore and context for thematic consistency:

```typescript
gen.setWorld({
  name: 'Aethermoor',
  description: 'A vast fantasy realm...',
  theme: 'High Fantasy with Steampunk',
  lore: '...',
  races: [...],
  classes: [...],
  // Add any custom context!
});
```

### 4. Generation

Generate single or multiple entity types:

```typescript
// Generate specific entities
await gen.generate('NPC', 10);

// Generate entire world (respects dependencies)
await gen.generateWorld({
  Race: 4,
  Class: 5,
  Zone: 3,
  NPC: 20,
  Enemy: 15,
  Item: 50,
  Quest: 10,
});
```

### 5. Interactive Editing

Edit during generation:

```typescript
await gen.generate('NPC', 5, {
  onEachGenerated: async (type, data, index, total) => {
    console.log(`Review ${data.name}? (${index}/${total})`);

    // Return edited data, null to regenerate, or undefined to keep as-is
    const edited = await askUserForEdits(data);
    return edited;
  }
});
```

Edit after generation:

```typescript
// Simple edit
await gen.edit('NPC', 'npc_123', {
  personality: 'Now mysterious and cryptic',
});

// Edit and see what's affected
const result = await gen.edit('Zone', 'zone_1', {
  description: 'Now has ancient ruins!',
});

console.log(result.affectedEntities.direct); // NPCs, Enemies in this zone
console.log(result.affectedEntities.indirect); // Quests involving those NPCs
```

### 6. Smart Regeneration

Automatically regenerate affected content:

```typescript
await gen.editAndRegenerate('NPC', 'npc_123', {
  faction: 'new_faction',
}, {
  regenerateDirect: true, // Regenerate quests from this NPC
  regenerateIndirect: true, // Regenerate quests that reference those quests
});
```

---

## 🎯 Example: Complete MMORPG World

See `examples/complete-example.ts` for a full example that generates:

- ✅ Races & Classes
- ✅ Professions
- ✅ Factions
- ✅ Zones with lore
- ✅ NPCs with dialogue
- ✅ Enemies with abilities
- ✅ Items with crafting recipes
- ✅ Interconnected quest chains

Run it:

```bash
npm run example
```

---

## 🛠️ Advanced Usage

### Custom LLM Configuration

```typescript
const gen = new GameDataGen({
  model: 'gpt-4o',
  temperature: 0.9,
  apiKey: process.env.OPENAI_API_KEY,
});

// Update later
gen.engine.updateConfig({
  temperature: 0.7,
});
```

### Dependency Tracking

```typescript
// Get what an entity depends on
const deps = gen.getDependencies('Quest', 'quest_123');
console.log(deps); // [NPC, Items, Enemies it references]

// Get what depends on an entity
const affected = gen.getAffected('NPC', 'npc_123');
console.log(affected.direct); // Quests from this NPC
console.log(affected.indirect); // Quests that chain from those quests
```

### Validation

```typescript
// Validate all relationships
const validation = gen.validateRelationships();

if (!validation.valid) {
  console.log('Broken links:', validation.brokenLinks);
}
```

### Import/Export

```typescript
// Save everything
await gen.saveToFile('./my-world.json');

// Load it back
await gen.loadFromFile('./my-world.json');

// Or use the data directly
const data = gen.export();
console.log(data.worldContext);
console.log(data.entities);
```

---

## 📖 API Reference

### GameDataGen Class

#### Schema Management
- `registerSchema(config)` - Register an entity schema
- `defineRelationship(config)` - Define entity relationships

#### World Context
- `setWorld(context)` - Set world context
- `updateWorld(updates)` - Update world context
- `getWorld()` - Get current world context

#### Content Generation
- `generate(entityType, count, options?)` - Generate entities
- `generateWorld(counts, options?)` - Generate entire world

#### Content Editing
- `edit(type, id, updates, options?)` - Edit an entity
- `getAffected(type, id)` - Get affected entities
- `regenerateAffected(affected, options?)` - Regenerate affected content
- `editAndRegenerate(type, id, updates, options?)` - Edit + auto-regenerate

#### Content Retrieval
- `getEntity(type, id)` - Get specific entity
- `getEntities(type)` - Get all entities of a type
- `getAllEntities()` - Get all entities
- `getStats()` - Get generation statistics

#### Data Management
- `export()` - Export all data
- `import(data)` - Import data
- `saveToFile(path)` - Save to JSON file
- `loadFromFile(path)` - Load from JSON file

#### Validation
- `validateRelationships()` - Check for broken links
- `getDependencies(type, id)` - Get dependency chain
- `clear()` - Clear generated content
- `reset()` - Reset everything

---

## 🏗️ Architecture

```
GameDataGen
├── SchemaRegistry     - Manages user-defined schemas
├── RelationshipManager - Tracks entity relationships
├── ContextManager     - Maintains world state and lore
├── GenerationEngine   - LlamaIndex + OpenAI integration
└── EditingSystem      - Handles edits and regeneration
```

---

## 🤝 Contributing

This is a framework for **your game**. Fork it, customize it, make it yours!

Some ideas:
- Add more example schemas
- Create schemas for different game genres (roguelike, strategy, etc.)
- Add support for other LLM providers
- Build a UI for visual editing
- Add import from existing game data formats

---

## 📝 License

ISC

---

## 🎮 Built For Game Developers

Whether you're building an MMORPG, RPG, roguelike, or any game that needs rich, interconnected content - GameDataGen helps you create worlds at scale while maintaining consistency and quality.

**Stop writing content. Start generating worlds.** 🌍✨
