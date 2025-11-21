import { GameDataGen } from '../src/GameDataGen.js';
import {
  globalIconify,
  getGameIcon,
  suggestIconForEntity,
  GAME_ICON_PACKS,
  IconifyIcon,
} from '../src/utils/IconifyService.js';
import { z } from 'zod';

/**
 * Example: Automatic icon assignment and downloading from Iconify
 */

// ============================================================
// Enhanced schemas with icon support
// ============================================================

const ItemWithIconSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['weapon', 'armor', 'consumable', 'material']),
  description: z.string(),
  rarity: z.enum(['common', 'uncommon', 'rare', 'epic', 'legendary']),
  // Icon info
  icon: z
    .object({
      prefix: z.string(), // 'game-icons', 'mdi', etc.
      name: z.string(), // Icon name
      color: z.string().optional(), // Hex color
    })
    .optional(),
});

const SpellWithIconSchema = z.object({
  id: z.string(),
  name: z.string(),
  school: z.enum(['fire', 'ice', 'nature', 'arcane']),
  description: z.string(),
  manaCost: z.number(),
  // Icon info
  icon: z
    .object({
      prefix: z.string(),
      name: z.string(),
      color: z.string().optional(),
    })
    .optional(),
});

async function main() {
  console.log('🎨 Iconify Integration Example\n');

  const gen = new GameDataGen({
    model: 'gpt-4o-mini',
    temperature: 0.8,
  });

  // ============================================================
  // 1. Show Available Icon Packs
  // ============================================================

  console.log('📦 Available Icon Packs:\n');

  console.log('Weapons:');
  for (const [key, icon] of Object.entries(GAME_ICON_PACKS.weapons)) {
    const url = globalIconify.getIconUrl(icon);
    console.log(`  ${key}: ${url}`);
  }

  console.log('\nMagic Spells:');
  for (const [key, icon] of Object.entries(GAME_ICON_PACKS.magic)) {
    const url = globalIconify.getIconUrl(icon);
    console.log(`  ${key}: ${url}`);
  }

  console.log('\nConsumables:');
  for (const [key, icon] of Object.entries(GAME_ICON_PACKS.consumables)) {
    const url = globalIconify.getIconUrl(icon);
    console.log(`  ${key}: ${url}`);
  }

  console.log();

  // ============================================================
  // 2. Register Schemas with Icons
  // ============================================================

  gen
    .registerSchema({
      name: 'ItemWithIcon',
      schema: ItemWithIconSchema,
      description: 'Items with Iconify icons',
    })
    .registerSchema({
      name: 'SpellWithIcon',
      schema: SpellWithIconSchema,
      description: 'Spells with Iconify icons',
    });

  gen.setWorld({
    name: 'Icon Test World',
    theme: 'Fantasy RPG with beautiful icons',
  });

  // ============================================================
  // 3. Generate Items with Manual Icon Assignment
  // ============================================================

  console.log('⚔️  Generating items with icons...\n');

  // Create sample items with manually assigned icons
  const sampleItems = [
    {
      id: 'sword_of_fire',
      name: 'Sword of Fire',
      type: 'weapon',
      description: 'A blazing sword forged in dragon fire',
      rarity: 'epic',
      icon: { prefix: 'game-icons', name: 'sword', color: 'ff4500' }, // Orange-red
    },
    {
      id: 'healing_potion',
      name: 'Greater Healing Potion',
      type: 'consumable',
      description: 'Restores 500 HP',
      rarity: 'common',
      icon: { prefix: 'game-icons', name: 'health-potion', color: 'ff0000' }, // Red
    },
    {
      id: 'steel_helmet',
      name: 'Steel Helmet',
      type: 'armor',
      description: 'Sturdy steel protection for your head',
      rarity: 'uncommon',
      icon: { prefix: 'game-icons', name: 'helmet', color: 'c0c0c0' }, // Silver
    },
  ];

  // Store items in context (simulate generation)
  for (const item of sampleItems) {
    gen.context.addEntity({
      id: item.id,
      type: 'ItemWithIcon',
      data: item,
      metadata: { generatedAt: new Date() },
    });

    console.log(`✓ ${item.name} (${item.rarity})`);
    console.log(`  Icon: ${item.icon.prefix}/${item.icon.name}`);
    console.log(
      `  URL: ${globalIconify.getIconUrl(item.icon as IconifyIcon)}`
    );
  }

  console.log();

  // ============================================================
  // 4. Download Icons to Files
  // ============================================================

  console.log('💾 Downloading icons as SVG files...\n');

  const iconsToDownload: IconifyIcon[] = sampleItems.map(
    (item) => item.icon as IconifyIcon
  );

  const filepaths = await globalIconify.saveIcons(
    iconsToDownload,
    './output/icons'
  );

  console.log(`✓ Downloaded ${filepaths.length} icons:`);
  for (const filepath of filepaths) {
    console.log(`  ${filepath}`);
  }

  console.log();

  // ============================================================
  // 5. Auto-Suggest Icons Based on Entity Type
  // ============================================================

  console.log('🤖 Auto-suggesting icons based on entity type...\n');

  const entityTypesToTest = [
    { type: 'weapon', data: { name: 'Axe' } },
    { type: 'armor', data: { name: 'Chestplate' } },
    { type: 'potion', data: { name: 'Mana Potion' } },
    { type: 'spell', data: { name: 'Fireball' } },
    { type: 'quest', data: { name: 'Kill 10 Rats' } },
    { type: 'npc', data: { name: 'Merchant' } },
    { type: 'enemy', data: { name: 'Dragon' } },
  ];

  for (const entity of entityTypesToTest) {
    const suggestedIcon = suggestIconForEntity(entity.type, entity.data);
    const url = globalIconify.getIconUrl(suggestedIcon);

    console.log(`${entity.type}:`);
    console.log(`  Suggested: ${suggestedIcon.prefix}/${suggestedIcon.name}`);
    console.log(`  URL: ${url}`);
  }

  console.log();

  // ============================================================
  // 6. Download from Predefined Packs
  // ============================================================

  console.log('📥 Downloading complete icon packs...\n');

  // Download all weapon icons
  const weaponIcons = Object.values(GAME_ICON_PACKS.weapons);
  console.log(`Downloading ${weaponIcons.length} weapon icons...`);

  const weaponPaths = await globalIconify.saveIcons(
    weaponIcons,
    './output/icons/weapons'
  );
  console.log(`✓ Saved to ./output/icons/weapons/`);

  // Download all magic icons
  const magicIcons = Object.values(GAME_ICON_PACKS.magic);
  console.log(`Downloading ${magicIcons.length} magic icons...`);

  const magicPaths = await globalIconify.saveIcons(
    magicIcons,
    './output/icons/magic'
  );
  console.log(`✓ Saved to ./output/icons/magic/`);

  console.log();

  // ============================================================
  // 7. Custom Icon Parameters
  // ============================================================

  console.log('🎨 Downloading icons with custom parameters...\n');

  const customIcons: IconifyIcon[] = [
    {
      prefix: 'game-icons',
      name: 'dragon',
      color: 'ff0000', // Red dragon
      width: 64,
      height: 64,
    },
    {
      prefix: 'game-icons',
      name: 'shield',
      color: '0000ff', // Blue shield
      rotate: 90,
    },
    {
      prefix: 'game-icons',
      name: 'sword',
      color: 'ffd700', // Gold sword
      flip: 'horizontal',
    },
  ];

  for (const icon of customIcons) {
    const url = globalIconify.getIconUrl(icon);
    console.log(`${icon.prefix}/${icon.name}:`);
    console.log(`  Color: #${icon.color}`);
    if (icon.width) console.log(`  Size: ${icon.width}x${icon.height}`);
    if (icon.rotate) console.log(`  Rotation: ${icon.rotate}°`);
    if (icon.flip) console.log(`  Flip: ${icon.flip}`);
    console.log(`  URL: ${url}`);

    // Download
    await globalIconify.saveIcon(icon, './output/icons/custom');
  }

  console.log(`✓ Saved to ./output/icons/custom/`);
  console.log();

  // ============================================================
  // 8. Batch Download Performance
  // ============================================================

  console.log('⚡ Performance test: Batch downloading...\n');

  const allIcons = [
    ...Object.values(GAME_ICON_PACKS.weapons),
    ...Object.values(GAME_ICON_PACKS.armor),
    ...Object.values(GAME_ICON_PACKS.consumables),
    ...Object.values(GAME_ICON_PACKS.magic),
  ];

  console.log(`Downloading ${allIcons.length} icons in parallel...`);

  const startTime = Date.now();
  const svgMap = await globalIconify.downloadIcons(allIcons);
  const elapsed = Date.now() - startTime;

  console.log(`✓ Downloaded ${svgMap.size} icons in ${elapsed}ms`);
  console.log(
    `  Average: ${(elapsed / svgMap.size).toFixed(2)}ms per icon`
  );

  // Show cache stats
  const cacheStats = globalIconify.getCacheStats();
  console.log(`  Cache size: ${cacheStats.size} icons`);

  console.log();

  // ============================================================
  // 9. Generate Icon Manifest
  // ============================================================

  console.log('📄 Generating icon manifest...\n');

  const manifest = {
    generated: new Date().toISOString(),
    totalIcons: cacheStats.size,
    categories: {
      weapons: Object.keys(GAME_ICON_PACKS.weapons),
      armor: Object.keys(GAME_ICON_PACKS.armor),
      consumables: Object.keys(GAME_ICON_PACKS.consumables),
      resources: Object.keys(GAME_ICON_PACKS.resources),
      magic: Object.keys(GAME_ICON_PACKS.magic),
      enemies: Object.keys(GAME_ICON_PACKS.enemies),
      npcs: Object.keys(GAME_ICON_PACKS.npcs),
      ui: Object.keys(GAME_ICON_PACKS.ui),
    },
    icons: cacheStats.icons.map((key) => {
      const [prefix, name] = key.split(':');
      return {
        key,
        prefix,
        name,
        url: globalIconify.getIconUrl({ prefix, name }),
      };
    }),
  };

  const fs = await import('fs/promises');
  await fs.writeFile(
    './output/icons/manifest.json',
    JSON.stringify(manifest, null, 2)
  );

  console.log('✓ Saved icon manifest to ./output/icons/manifest.json');
  console.log(`  Total icons cataloged: ${manifest.icons.length}`);

  console.log();

  // ============================================================
  // 10. Usage Examples
  // ============================================================

  console.log('💡 Usage Examples:\n');

  console.log('```typescript');
  console.log('// 1. Get a specific icon from a pack');
  console.log('const sword = getGameIcon("weapons", "sword");');
  console.log('const url = globalIconify.getIconUrl(sword);');
  console.log('');
  console.log('// 2. Download an icon');
  console.log('await globalIconify.saveIcon(sword, "./icons");');
  console.log('');
  console.log('// 3. Auto-suggest icon for entity');
  console.log('const icon = suggestIconForEntity("weapon", item);');
  console.log('');
  console.log('// 4. Custom colored icon');
  console.log('const redDragon = {');
  console.log('  prefix: "game-icons",');
  console.log('  name: "dragon",');
  console.log('  color: "ff0000"');
  console.log('};');
  console.log('```');

  console.log('\n✅ Icon integration complete!\n');
}

main().catch(console.error);
