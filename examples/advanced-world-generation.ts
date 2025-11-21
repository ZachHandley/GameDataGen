import { GameDataGen } from '../src/GameDataGen.js';
import { globalKnowledgeGraph } from '../src/core/KnowledgeGraph.js';
import { initializeLevelingSystem } from '../src/core/LevelingSystem.js';
import {
  EnhancedZoneSchema,
  EnhancedNPCSchema,
  DungeonSchema,
  QuestlineSchema,
  WorldBossSchema,
  EnhancedItemSchema,
  SpellSchema,
} from '../src/schemas/examples/enhanced-mmorpg-schemas.js';

/**
 * Advanced example showing:
 * - Knowledge graph relationships (including optional relationships)
 * - Leveling system with XP budgeting
 * - Spatial placement
 * - Composite entities (dungeons)
 * - Complex questlines
 */

async function main() {
  console.log('🌍 Advanced World Generation Example\n');

  // ============================================================
  // 1. Initialize with Leveling System
  // ============================================================

  const gen = new GameDataGen({
    model: 'gpt-4o-mini',
    temperature: 0.8,
  });

  // Set up leveling system
  const levelingSystem = initializeLevelingSystem(
    {
      maxLevel: 60,
      baseXP: 100,
      xpCurve: 'exponential',
    },
    {
      mainQuests: 0.35, // 35% of XP from main story
      sideQuests: 0.15,
      dungeons: 0.25,
      raids: 0.05,
      gathering: 0.05,
      crafting: 0.03,
      exploration: 0.05,
      worldBosses: 0.04,
      dailies: 0.02,
      other: 0.01,
    }
  );

  console.log('📊 Leveling System Configured:');
  console.log(`   Max Level: ${levelingSystem.getConfig().maxLevel}`);
  console.log(`   Total XP Needed: ${levelingSystem.getTotalXPNeeded()}`);
  console.log(`   Main Quest XP Budget: ${levelingSystem.getXPBudget('mainQuests')}`);
  console.log();

  // ============================================================
  // 2. Set World Context
  // ============================================================

  gen.setWorld({
    name: 'Aethermoor',
    description: 'A high-fantasy realm with magical technology',
    theme: 'High Fantasy + Steampunk',
    maxLevel: 60,
    lore: `
      The world of Aethermoor is divided into distinct biomes, each shaped by
      ancient magic and modern technology. Players will journey from the
      Verdant Forests to the Scorched Wastelands, uncovering the mysteries
      of the Great Sundering.
    `,
  });

  // ============================================================
  // 3. Register Enhanced Schemas
  // ============================================================

  console.log('📋 Registering schemas...');

  gen
    .registerSchema({
      name: 'Zone',
      schema: EnhancedZoneSchema,
      description: 'Enhanced zones with spatial data',
      generationPriority: 1,
    })
    .registerSchema({
      name: 'Spell',
      schema: SpellSchema,
      description: 'Spells that can be cast',
      generationPriority: 2,
    })
    .registerSchema({
      name: 'Item',
      schema: EnhancedItemSchema,
      description: 'Items with optional spell slots',
      generationPriority: 3,
    })
    .registerSchema({
      name: 'NPC',
      schema: EnhancedNPCSchema,
      description: 'NPCs with tasklists and spatial awareness',
      dependencies: ['Zone'],
      generationPriority: 4,
    })
    .registerSchema({
      name: 'WorldBoss',
      schema: WorldBossSchema,
      description: 'Powerful world bosses',
      dependencies: ['Zone'],
      generationPriority: 5,
    })
    .registerSchema({
      name: 'Dungeon',
      schema: DungeonSchema,
      description: 'Dungeons with multiple rooms',
      dependencies: ['Zone', 'Item'],
      generationPriority: 6,
    })
    .registerSchema({
      name: 'Questline',
      schema: QuestlineSchema,
      description: 'Chains of quests',
      dependencies: ['NPC', 'Dungeon'],
      generationPriority: 7,
    });

  console.log('✓ Schemas registered\n');

  // ============================================================
  // 4. Generate Content
  // ============================================================

  console.log('🎲 Generating world content...\n');

  // Calculate how much content we need based on XP budget
  const avgQuestXP = levelingSystem.calculateQuestXP(30, 'main'); // Average level 30
  const mainQuestCount = levelingSystem.calculateContentCount(
    'mainQuests',
    avgQuestXP
  );

  console.log(`📈 Need ${mainQuestCount} main quests to fill XP budget\n`);

  // Generate zones with level ranges
  const zoneLevelRanges = levelingSystem.suggestZoneLevelRanges(5);
  console.log('🗺️  Suggested zone level ranges:');
  zoneLevelRanges.forEach((range, i) => {
    console.log(`   Zone ${i + 1}: Levels ${range.min}-${range.max}`);
  });
  console.log();

  // Generate the world
  const result = await gen.generateWorld({
    Zone: 3,
    Spell: 20,
    Item: 15,
    NPC: 10,
    WorldBoss: 2,
    Dungeon: 2,
    Questline: 1,
  });

  console.log('✓ World generation complete!\n');

  // ============================================================
  // 5. Add Knowledge Graph Relationships
  // ============================================================

  console.log('🔗 Adding knowledge graph relationships...\n');

  // Example: Weapon can cast spells (optional relationship)
  const items = gen.getEntities('Item');
  const spells = gen.getEntities('Spell');

  if (items.length > 0 && spells.length > 0) {
    const weapon = items.find((i) => i.data.type === 'weapon');
    const fireball = spells.find((s) => s.data.school === 'fire');

    if (weapon && fireball) {
      globalKnowledgeGraph.addTriplet({
        subject: { type: 'Item', id: weapon.id },
        predicate: 'can_cast',
        object: { type: 'Spell', id: fireball.id },
        metadata: {
          optional: true, // This is an optional spell slot
          charges: 5,
          cooldown: 30, // seconds
          levelRequired: 10,
        },
      });

      console.log(
        `✓ ${weapon.data.name} can cast ${fireball.data.name} (optional, 5 charges)`
      );
    }
  }

  // Example: World boss drops legendary item
  const bosses = gen.getEntities('WorldBoss');
  const legendaryItem = items.find((i) => i.data.rarity === 'legendary');

  if (bosses.length > 0 && legendaryItem) {
    globalKnowledgeGraph.addTriplet({
      subject: { type: 'WorldBoss', id: bosses[0].id },
      predicate: 'drops',
      object: { type: 'Item', id: legendaryItem.id },
      metadata: {
        chance: 0.05, // 5% drop chance
        quantity: 1,
        guaranteed: false,
      },
    });

    console.log(
      `✓ ${bosses[0].data.name} drops ${legendaryItem.data.name} (5% chance)`
    );
  }

  // Example: NPC is located at specific coordinates
  const npcs = gen.getEntities('NPC');
  const zones = gen.getEntities('Zone');

  if (npcs.length > 0 && zones.length > 0) {
    globalKnowledgeGraph.addTriplet({
      subject: { type: 'NPC', id: npcs[0].id },
      predicate: 'located_at',
      object: { type: 'Zone', id: zones[0].id },
      metadata: {
        coordinates: { x: 100, y: 200, z: 5 },
        schedule: [
          {
            time: '08:00',
            action: 'fetch_water',
            location: { x: 105, y: 210 },
            duration: 300, // 5 minutes
          },
          {
            time: '09:00',
            action: 'work',
            location: { x: 95, y: 195 },
            duration: 3600, // 1 hour
          },
        ],
      },
    });

    console.log(`✓ ${npcs[0].data.name} located at ${zones[0].data.name} with daily tasks`);
  }

  // Example: Questline leads to dungeon
  const questlines = gen.getEntities('Questline');
  const dungeons = gen.getEntities('Dungeon');

  if (questlines.length > 0 && dungeons.length > 0) {
    globalKnowledgeGraph.addTriplet({
      subject: { type: 'Questline', id: questlines[0].id },
      predicate: 'culminates_in',
      object: { type: 'Dungeon', id: dungeons[0].id },
      metadata: {
        type: 'finale',
        levelRequired: 25,
        requiredQuests: [], // All quests in the chain
      },
    });

    console.log(
      `✓ ${questlines[0].data.name} culminates in ${dungeons[0].data.name}`
    );
  }

  console.log();

  // ============================================================
  // 6. Query Knowledge Graph
  // ============================================================

  console.log('🔍 Querying knowledge graph...\n');

  // Find all items that can cast spells
  const itemsWithSpells = globalKnowledgeGraph.find({
    predicate: 'can_cast',
  });

  console.log(`Items with spell abilities: ${itemsWithSpells.length}`);
  for (const triplet of itemsWithSpells) {
    const item = gen.getEntity(triplet.subject.type, triplet.subject.id);
    const spell = gen.getEntity(triplet.object.type, triplet.object.id);
    console.log(
      `  - ${item?.data.name} → ${spell?.data.name} (${triplet.metadata?.optional ? 'optional' : 'built-in'})`
    );
  }

  console.log();

  // Get loot drops for world boss
  if (bosses.length > 0) {
    const loot = globalKnowledgeGraph.getLootDrops('WorldBoss', bosses[0].id, 60);
    console.log(`Loot from ${bosses[0].data.name}:`);
    for (const drop of loot) {
      const item = gen.getEntity(drop.item.type, drop.item.id);
      console.log(
        `  - ${item?.data.name} x${drop.quantity} ${drop.rolled ? '(dropped!)' : '(not dropped)'}`
      );
    }
  }

  console.log();

  // ============================================================
  // 7. Validate XP Budget
  // ============================================================

  console.log('🎯 Validating XP budget...\n');

  const validation = levelingSystem.validateXPBudget({
    mainQuestCount: 50,
    sideQuestCount: 100,
    dungeonCount: 10,
    averageQuestLevel: 30,
    averageDungeonLevel: 35,
  });

  if (validation.valid) {
    console.log('✅ XP budget is satisfied! Players can reach max level.');
  } else {
    console.log('⚠️  XP budget deficit:');
    console.log(`   Required: ${validation.totalRequiredXP} XP`);
    console.log(`   Available: ${validation.totalAvailableXP} XP`);
    console.log(`   Deficit: ${validation.deficit} XP`);
    console.log('\n   Suggestions:');
    for (const suggestion of validation.suggestions) {
      console.log(`   - ${suggestion}`);
    }
  }

  console.log();

  // ============================================================
  // 8. Knowledge Graph Stats
  // ============================================================

  const graphStats = globalKnowledgeGraph.getStats();
  console.log('📊 Knowledge Graph Statistics:');
  console.log(`   Total relationships: ${graphStats.totalTriplets}`);
  console.log('   Relationship types:');
  for (const [pred, count] of Object.entries(graphStats.predicateCount)) {
    console.log(`     - ${pred}: ${count}`);
  }

  console.log();

  // ============================================================
  // 9. Export Everything
  // ============================================================

  console.log('💾 Exporting world data...');

  const worldData = gen.export();
  const graphData = globalKnowledgeGraph.export();

  await gen.saveToFile('./output/advanced-world.json');

  // Save knowledge graph separately
  const fs = await import('fs/promises');
  await fs.writeFile(
    './output/knowledge-graph.json',
    JSON.stringify(graphData, null, 2)
  );

  console.log('   ✓ Saved to output/advanced-world.json');
  console.log('   ✓ Saved knowledge graph to output/knowledge-graph.json');

  console.log('\n✅ Complete!\n');
}

main().catch(console.error);
