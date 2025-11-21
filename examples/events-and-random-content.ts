import { GameDataGen } from '../src/GameDataGen.js';
import { globalKnowledgeGraph, Triplet } from '../src/core/KnowledgeGraph.js';
import {
  EventSchema,
  EventBossSchema,
  RandomEncounterSchema,
} from '../src/schemas/examples/events-and-random-schemas.js';

/**
 * Example: How events, event bosses, and random encounters tie into the knowledge graph
 */

async function main() {
  console.log('🎪 Events & Random Content Example\n');

  const gen = new GameDataGen({
    model: 'gpt-4o-mini',
    temperature: 0.9,  // Higher for more creative events
  });

  // ============================================================
  // 1. Register Event Schemas
  // ============================================================

  console.log('📋 Registering event schemas...');

  gen
    .registerSchema({
      name: 'Event',
      schema: EventSchema,
      description: 'Seasonal and world events',
      generationPriority: 10,
    })
    .registerSchema({
      name: 'EventBoss',
      schema: EventBossSchema,
      description: 'Event-specific bosses',
      generationPriority: 11,
    })
    .registerSchema({
      name: 'RandomEncounter',
      schema: RandomEncounterSchema,
      description: 'Random encounters while playing',
      generationPriority: 12,
    });

  console.log('✓ Event schemas registered\n');

  // ============================================================
  // 2. Generate Sample Event Content
  // ============================================================

  console.log('🎲 Generating events...\n');

  gen.setWorld({
    name: 'Aethermoor',
    theme: 'High Fantasy with Seasonal Events',
    lore: 'The world celebrates ancient festivals and battles random chaos rifts.',
  });

  // Generate some events
  const eventResult = await gen.generate('Event', 1, {
    specifications: {
      name: 'Winter\'s End Festival',
      type: 'seasonal',
      activationConditions: {
        startDate: '2025-12-15',
        endDate: '2026-01-05',
        minLevel: 10,
      },
    },
  });

  const encounterResult = await gen.generate('RandomEncounter', 1, {
    specifications: {
      type: 'mystery_event',
      triggerConditions: {
        baseChance: 0.02,  // 2% chance per minute
        timeOfDay: 'night',
      },
    },
  });

  if (!eventResult.success || !encounterResult.success) {
    console.error('Generation failed');
    return;
  }

  const winterEvent = eventResult.entities[0];
  const mysteryEncounter = encounterResult.entities[0];

  console.log(`✓ Generated event: ${winterEvent.data.name}`);
  console.log(`✓ Generated encounter: ${mysteryEncounter.data.name}\n`);

  // ============================================================
  // 3. Add Knowledge Graph Relationships for Events
  // ============================================================

  console.log('🔗 Defining event relationships...\n');

  // Example 1: Event spawns boss
  // (Event) --spawns--> (Boss) with schedule metadata

  const fakeEventBossId = 'boss_frost_giant';

  globalKnowledgeGraph.addTriplet({
    subject: { type: 'Event', id: winterEvent.id },
    predicate: 'spawns',
    object: { type: 'EventBoss', id: fakeEventBossId },
    metadata: {
      schedule: '0 20 * * 6',  // Every Saturday at 8PM
      announceSpawn: true,
      guaranteed: true,  // Always spawns during event
      spawnLocation: {
        zone: 'frozen_peaks',
        coordinates: { x: 500, y: 300 },
      },
    },
  });

  console.log(`✓ ${winterEvent.data.name} spawns Frost Giant boss (Saturdays 8PM)`);

  // Example 2: Event modifies zones
  // (Event) --modifies--> (Zone) with decoration metadata

  globalKnowledgeGraph.addTriplet({
    subject: { type: 'Event', id: winterEvent.id },
    predicate: 'modifies',
    object: { type: 'Zone', id: 'zone_capital_city' },
    metadata: {
      decoration: 'winter_decorations',
      weatherOverride: 'snow',
      musicOverride: 'festive_music',
      duration: 'event_active',  // While event is active
    },
  });

  console.log(`✓ ${winterEvent.data.name} modifies Capital City (snow + decorations)`);

  // Example 3: Event provides limited-time items
  // (Event) --offers--> (Item) with availability metadata

  const fakeLimitedItemId = 'item_winter_cloak';

  globalKnowledgeGraph.addTriplet({
    subject: { type: 'Event', id: winterEvent.id },
    predicate: 'offers',
    object: { type: 'Item', id: fakeLimitedItemId },
    metadata: {
      optional: false,  // Always available during event
      vendorNPC: 'npc_festival_merchant',
      stock: 1,  // Limited to 1 per player
      expiresWithEvent: true,  // Can't get after event ends
      cost: 500,  // Gold
    },
  });

  console.log(`✓ ${winterEvent.data.name} offers Winter Cloak (limited-time item)`);

  // Example 4: Random encounter triggers quest
  // (RandomEncounter) --triggers--> (Quest) with condition metadata

  const fakeQuestId = 'quest_investigate_rift';

  globalKnowledgeGraph.addTriplet({
    subject: { type: 'RandomEncounter', id: mysteryEncounter.id },
    predicate: 'triggers',
    object: { type: 'Quest', id: fakeQuestId },
    metadata: {
      chance: 0.3,  // 30% chance to trigger quest
      oneTimeOnly: true,  // Can only trigger once per character
      levelRequired: 25,
    },
  });

  console.log(`✓ ${mysteryEncounter.data.name} can trigger "Investigate Rift" quest (30%)`);

  // Example 5: Event has prerequisites
  // (Event) --requires--> (Quest) for activation

  const fakePrereqQuestId = 'quest_winter_preparation';

  globalKnowledgeGraph.addTriplet({
    subject: { type: 'Event', id: winterEvent.id },
    predicate: 'requires',
    object: { type: 'Quest', id: fakePrereqQuestId },
    metadata: {
      required: true,
      type: 'prerequisite',
      description: 'Must complete "Winter Preparation" to participate',
    },
  });

  console.log(`✓ ${winterEvent.data.name} requires "Winter Preparation" quest\n`);

  // ============================================================
  // 4. Query Event Relationships
  // ============================================================

  console.log('🔍 Querying event relationships...\n');

  // Find all bosses spawned by events
  const eventBosses = globalKnowledgeGraph.find({
    predicate: 'spawns',
  });

  console.log('Event Bosses:');
  for (const triplet of eventBosses) {
    const event = gen.getEntity(triplet.subject.type, triplet.subject.id);
    console.log(`  - ${event?.data.name} spawns boss at ${triplet.metadata?.spawnLocation?.zone}`);
    if (triplet.metadata?.schedule) {
      console.log(`    Schedule: ${triplet.metadata.schedule}`);
    }
  }

  console.log();

  // Find all zones modified by events
  const modifiedZones = globalKnowledgeGraph.find({
    predicate: 'modifies',
  });

  console.log('Zone Modifications:');
  for (const triplet of modifiedZones) {
    const event = gen.getEntity(triplet.subject.type, triplet.subject.id);
    console.log(`  - ${event?.data.name}:`);
    console.log(`    Decoration: ${triplet.metadata?.decoration}`);
    console.log(`    Weather: ${triplet.metadata?.weatherOverride}`);
  }

  console.log();

  // Find items offered during events
  const eventItems = globalKnowledgeGraph.find({
    predicate: 'offers',
  });

  console.log('Event-Limited Items:');
  for (const triplet of eventItems) {
    const event = gen.getEntity(triplet.subject.type, triplet.subject.id);
    console.log(`  - ${triplet.object.id} (from ${event?.data.name})`);
    console.log(`    Cost: ${triplet.metadata?.cost} gold`);
    console.log(`    Stock: ${triplet.metadata?.stock} per player`);
  }

  console.log();

  // ============================================================
  // 5. Simulate Event Activation
  // ============================================================

  console.log('⚡ Simulating event activation...\n');

  // Check if event should be active
  const winterEventData = winterEvent.data;
  const now = new Date();
  const start = new Date(winterEventData.activationConditions.startDate);
  const end = new Date(winterEventData.activationConditions.endDate);

  const isActive = now >= start && now <= end;

  console.log(`Event: ${winterEventData.name}`);
  console.log(`Active: ${isActive ? 'YES' : 'NO'}`);
  console.log(`Period: ${start.toLocaleDateString()} - ${end.toLocaleDateString()}`);

  if (isActive) {
    console.log('\n📢 Event is ACTIVE! Applying effects...');

    // Get all relationships for this event
    const eventRelations = globalKnowledgeGraph.findBySubject('Event', winterEvent.id);

    console.log(`  - Found ${eventRelations.length} event effects`);

    for (const rel of eventRelations) {
      switch (rel.predicate) {
        case 'spawns':
          console.log(`  ✓ Spawning ${rel.object.id}...`);
          break;
        case 'modifies':
          console.log(`  ✓ Modifying ${rel.object.id}...`);
          break;
        case 'offers':
          console.log(`  ✓ Adding ${rel.object.id} to vendors...`);
          break;
      }
    }
  } else {
    console.log('\n⏸️  Event is not active.');
  }

  console.log();

  // ============================================================
  // 6. Simulate Random Encounter Trigger
  // ============================================================

  console.log('🎲 Simulating random encounter trigger...\n');

  const encounterData = mysteryEncounter.data;
  const playerLevel = 30;
  const currentZone = 'zone_dark_forest';
  const timeOfDay = 'night';

  // Check if encounter can trigger
  const canTrigger =
    encounterData.triggerConditions.zones?.includes(currentZone) &&
    encounterData.triggerConditions.timeOfDay === timeOfDay &&
    playerLevel >= (encounterData.triggerConditions.playerLevel?.min || 0) &&
    playerLevel <= (encounterData.triggerConditions.playerLevel?.max || 100);

  if (canTrigger) {
    const triggerRoll = Math.random();
    const triggered = triggerRoll < encounterData.triggerConditions.baseChance;

    console.log(`Encounter: ${encounterData.name}`);
    console.log(`Can trigger: YES`);
    console.log(`Chance: ${encounterData.triggerConditions.baseChance * 100}%`);
    console.log(`Roll: ${(triggerRoll * 100).toFixed(2)}%`);
    console.log(`Result: ${triggered ? '🎯 TRIGGERED!' : '❌ Not triggered'}`);

    if (triggered) {
      // Check if it triggers a quest
      const questTriggers = globalKnowledgeGraph.find({
        subject: { type: 'RandomEncounter', id: mysteryEncounter.id },
        predicate: 'triggers',
      });

      if (questTriggers.length > 0) {
        const questRoll = Math.random();
        const questTriggered = questRoll < (questTriggers[0].metadata?.chance || 0);

        console.log(`\n  Quest trigger roll: ${(questRoll * 100).toFixed(2)}%`);
        console.log(`  ${questTriggered ? '✨ Quest triggered!' : '📜 No quest triggered'}`);
      }
    }
  } else {
    console.log(`Encounter: ${encounterData.name}`);
    console.log(`Can trigger: NO (conditions not met)`);
  }

  console.log();

  // ============================================================
  // 7. Export Event Data
  // ============================================================

  console.log('💾 Exporting event data...');

  const worldData = gen.export();
  const graphData = globalKnowledgeGraph.export();

  const fs = await import('fs/promises');
  await gen.saveToFile('./output/events-world.json');
  await fs.writeFile(
    './output/events-knowledge-graph.json',
    JSON.stringify(graphData, null, 2)
  );

  console.log('  ✓ Saved to output/events-world.json');
  console.log('  ✓ Saved knowledge graph to output/events-knowledge-graph.json');

  console.log('\n✅ Complete!\n');

  // ============================================================
  // 8. Show How to Query Active Events
  // ============================================================

  console.log('📊 Example: Query all active events\n');

  console.log('```typescript');
  console.log('// Get all events');
  console.log('const events = gen.getEntities("Event");');
  console.log('');
  console.log('// Filter by active dates');
  console.log('const activeEvents = events.filter(event => {');
  console.log('  const now = new Date();');
  console.log('  const start = new Date(event.data.activationConditions.startDate);');
  console.log('  const end = new Date(event.data.activationConditions.endDate);');
  console.log('  return now >= start && now <= end;');
  console.log('});');
  console.log('');
  console.log('// For each active event, get its effects');
  console.log('for (const event of activeEvents) {');
  console.log('  const effects = globalKnowledgeGraph.findBySubject("Event", event.id);');
  console.log('  ');
  console.log('  // Apply each effect');
  console.log('  for (const effect of effects) {');
  console.log('    if (effect.predicate === "spawns") {');
  console.log('      spawnEventBoss(effect.object.id, effect.metadata);');
  console.log('    }');
  console.log('    else if (effect.predicate === "modifies") {');
  console.log('      modifyZone(effect.object.id, effect.metadata);');
  console.log('    }');
  console.log('  }');
  console.log('}');
  console.log('```');
}

main().catch(console.error);
