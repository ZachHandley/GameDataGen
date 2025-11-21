import { GameDataGen } from '../src/GameDataGen.js';
import { z } from 'zod';

/**
 * Simple example - Generate NPCs for a tavern
 */

async function main() {
  // Initialize
  const gen = new GameDataGen({
    model: 'gpt-4o-mini',
    temperature: 0.8,
  });

  // Define a simple NPC schema
  const TavernNPCSchema = z.object({
    id: z.string(),
    name: z.string(),
    role: z.enum(['bartender', 'patron', 'bard', 'innkeeper']),
    personality: z.string(),
    greeting: z.string(),
    backstory: z.string(),
  });

  // Register it
  gen.registerSchema({
    name: 'TavernNPC',
    schema: TavernNPCSchema,
    description: 'NPCs found in taverns',
  });

  // Set world context
  gen.setWorld({
    name: 'The Rusty Tankard Tavern',
    description: 'A cozy tavern in a small medieval town',
    lore: 'This tavern has been run by the same family for three generations. It serves as a meeting place for adventurers and locals alike.',
    theme: 'Medieval Fantasy',
  });

  console.log('🍺 Generating Tavern NPCs...\n');

  // Generate NPCs with interactive editing
  const result = await gen.generate('TavernNPC', 3, {
    onEachGenerated: async (type, data, index, total) => {
      console.log(`\n📝 Generated NPC ${index}/${total}:`);
      console.log(`   Name: ${data.name}`);
      console.log(`   Role: ${data.role}`);
      console.log(`   Personality: ${data.personality}`);
      console.log(`   Greeting: "${data.greeting}"`);

      // You could prompt for edits here
      // For now, just approve
      return data;
    },
  });

  if (result.success) {
    console.log('\n✅ Generation complete!\n');

    // Show all NPCs
    console.log('📋 All Tavern NPCs:');
    for (const npc of result.entities) {
      console.log(`\n${npc.data.name} (${npc.data.role})`);
      console.log(`  ${npc.data.backstory}`);
    }

    // Save to file
    await gen.saveToFile('./output/tavern-npcs.json');
    console.log('\n💾 Saved to output/tavern-npcs.json');
  } else {
    console.error('❌ Generation failed:', result.error);
  }
}

main().catch(console.error);
