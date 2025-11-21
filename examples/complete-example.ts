import { GameDataGen } from '../src/GameDataGen.js';
import {
  RaceSchema,
  ClassSchema,
  ProfessionSchema,
  FactionSchema,
  ZoneSchema,
  NPCSchema,
  EnemySchema,
  ItemSchema,
  QuestSchema,
} from '../src/schemas/examples/mmorpg-schemas.js';

/**
 * Complete example showing how to use GameDataGen
 */

async function main() {
  // ============================================================
  // 1. Initialize GameDataGen
  // ============================================================

  const gen = new GameDataGen({
    model: 'gpt-4o-mini',
    temperature: 0.8,
    apiKey: process.env.OPENAI_API_KEY,
  });

  console.log('🎮 GameDataGen Initialized\n');

  // ============================================================
  // 2. Register Schemas
  // ============================================================

  console.log('📋 Registering schemas...');

  // Foundation schemas (no dependencies)
  gen
    .registerSchema({
      name: 'Race',
      schema: RaceSchema,
      description: 'Playable races in the game',
      generationPriority: 1,
    })
    .registerSchema({
      name: 'Class',
      schema: ClassSchema,
      description: 'Playable classes/professions',
      generationPriority: 1,
    })
    .registerSchema({
      name: 'Profession',
      schema: ProfessionSchema,
      description: 'Crafting and gathering professions',
      generationPriority: 1,
    })
    .registerSchema({
      name: 'Faction',
      schema: FactionSchema,
      description: 'Factions in the world',
      generationPriority: 2,
    });

  // World building schemas
  gen.registerSchema({
    name: 'Zone',
    schema: ZoneSchema,
    description: 'Zones/regions in the world',
    dependencies: ['Faction'],
    generationPriority: 3,
  });

  // Character schemas
  gen
    .registerSchema({
      name: 'NPC',
      schema: NPCSchema,
      description: 'Non-player characters',
      dependencies: ['Race', 'Class', 'Faction', 'Zone'],
      generationPriority: 4,
    })
    .registerSchema({
      name: 'Enemy',
      schema: EnemySchema,
      description: 'Enemy creatures and monsters',
      dependencies: ['Zone', 'Faction'],
      generationPriority: 4,
    });

  // Items
  gen.registerSchema({
    name: 'Item',
    schema: ItemSchema,
    description: 'Items, weapons, armor, consumables',
    dependencies: ['Profession'],
    generationPriority: 5,
  });

  // Quests (depend on everything)
  gen.registerSchema({
    name: 'Quest',
    schema: QuestSchema,
    description: 'Quests and storylines',
    dependencies: ['NPC', 'Item', 'Enemy', 'Zone'],
    generationPriority: 6,
  });

  console.log('✓ Schemas registered\n');

  // ============================================================
  // 3. Define Relationships
  // ============================================================

  console.log('🔗 Defining relationships...');

  gen
    .defineRelationship({
      from: 'Zone',
      to: 'Faction',
      type: 'many-to-many',
      fieldName: 'factions',
      contextual: true,
    })
    .defineRelationship({
      from: 'NPC',
      to: 'Zone',
      type: 'many-to-one',
      fieldName: 'location.zone',
      contextual: true,
      required: true,
    })
    .defineRelationship({
      from: 'NPC',
      to: 'Race',
      type: 'many-to-one',
      fieldName: 'race',
      contextual: true,
    })
    .defineRelationship({
      from: 'NPC',
      to: 'Faction',
      type: 'many-to-one',
      fieldName: 'faction',
      contextual: true,
    })
    .defineRelationship({
      from: 'Enemy',
      to: 'Zone',
      type: 'many-to-one',
      fieldName: 'location.zone',
      contextual: true,
    })
    .defineRelationship({
      from: 'Quest',
      to: 'NPC',
      type: 'many-to-one',
      fieldName: 'questGiver',
      contextual: true,
    });

  console.log('✓ Relationships defined\n');

  // ============================================================
  // 4. Set World Context
  // ============================================================

  console.log('🌍 Setting world context...');

  gen.setWorld({
    name: 'Aethermoor',
    description:
      'A vast fantasy realm where magic and technology intertwine, shaped by ancient conflicts between celestial and infernal forces.',
    theme: 'High Fantasy with Steampunk elements',
    setting: 'Medieval fantasy world with magical technology',
    lore: `
      Thousands of years ago, the Great Sundering tore the fabric of reality,
      creating rifts between the mortal realm and the planes beyond. From these
      rifts came both wonders and horrors - celestial beings offering knowledge,
      and demons seeking conquest.

      The mortal races learned to harness Aether, the raw magical energy that
      flows through the rifts, combining it with technology to create a unique
      civilization. Now, as the rifts grow unstable once more, heroes must rise
      to prevent another Sundering.
    `,
  });

  console.log('✓ World context set\n');

  // ============================================================
  // 5. Generate Content
  // ============================================================

  console.log('🎲 Generating world content...\n');

  const worldGenResult = await gen.generateWorld(
    {
      Race: 4,
      Class: 5,
      Profession: 3,
      Faction: 3,
      Zone: 2,
      NPC: 5,
      Enemy: 4,
      Item: 10,
      Quest: 3,
    },
    {
      onEachGenerated: async (entityType, entity, index, total) => {
        console.log(`  ✓ Generated ${entityType} ${index}/${total}: ${entity.data.name}`);
      },
    }
  );

  if (!worldGenResult.success) {
    console.error('\n❌ Generation errors:', worldGenResult.errors);
    return;
  }

  console.log('\n✓ World generation complete!\n');

  // ============================================================
  // 6. Review Generated Content
  // ============================================================

  console.log('📊 Generation Statistics:');
  const stats = gen.getStats();
  console.log(`  Total entities: ${stats.totalEntities}`);
  for (const [type, count] of Object.entries(stats.entitiesByType)) {
    console.log(`  - ${type}: ${count}`);
  }
  console.log();

  // ============================================================
  // 7. Interactive Editing Example
  // ============================================================

  console.log('✏️  Editing example...');

  // Get a zone
  const zones = gen.getEntities('Zone');
  if (zones.length > 0) {
    const zone = zones[0];
    console.log(`  Original zone: ${zone.data.name}`);

    // Edit the zone
    const editResult = await gen.edit('Zone', zone.id, {
      description: zone.data.description + ' (Recently discovered ancient ruins here!)',
    });

    if (editResult.success) {
      console.log(`  ✓ Updated zone description`);

      // Check what's affected
      if (editResult.affectedEntities) {
        console.log(
          `  📍 Affected entities: ${editResult.affectedEntities.all.length}`
        );
        for (const affected of editResult.affectedEntities.direct) {
          console.log(`    - ${affected.type}: ${affected.data.name}`);
        }
      }
    }
  }
  console.log();

  // ============================================================
  // 8. Regenerate Affected Content
  // ============================================================

  console.log('🔄 Regeneration example...');

  const npcs = gen.getEntities('NPC');
  if (npcs.length > 0) {
    const npc = npcs[0];
    console.log(`  Editing NPC: ${npc.data.name}`);

    // Edit and auto-regenerate affected content
    const result = await gen.editAndRegenerate(
      'NPC',
      npc.id,
      {
        personality: 'Mysterious and cryptic, speaks in riddles',
      },
      {
        regenerateDirect: true, // Regenerate quests given by this NPC
      }
    );

    if (result.success) {
      console.log(`  ✓ NPC updated`);
      if (result.regenerated) {
        console.log(`  ✓ Regenerated ${result.regenerated.length} affected entities`);
      }
    }
  }
  console.log();

  // ============================================================
  // 9. Validate Relationships
  // ============================================================

  console.log('🔍 Validating relationships...');

  const validation = gen.validateRelationships();
  if (validation.valid) {
    console.log('  ✓ All relationships valid!');
  } else {
    console.log(`  ⚠️  Found ${validation.brokenLinks.length} broken links`);
    for (const broken of validation.brokenLinks) {
      console.log(
        `    - ${broken.from.type}:${broken.from.id} → ${broken.toType}:${broken.toId}`
      );
    }
  }
  console.log();

  // ============================================================
  // 10. Export Data
  // ============================================================

  console.log('💾 Exporting data...');

  await gen.saveToFile('./output/aethermoor-world.json');
  console.log('  ✓ Saved to output/aethermoor-world.json\n');

  // ============================================================
  // 11. Show Sample Content
  // ============================================================

  console.log('📖 Sample Generated Content:\n');

  const sampleZone = zones[0];
  if (sampleZone) {
    console.log('Zone Example:');
    console.log(JSON.stringify(sampleZone.data, null, 2));
    console.log();
  }

  const sampleQuest = gen.getEntities('Quest')[0];
  if (sampleQuest) {
    console.log('Quest Example:');
    console.log(JSON.stringify(sampleQuest.data, null, 2));
    console.log();
  }

  console.log('✅ Complete!\n');
}

// Run the example
main().catch(console.error);
