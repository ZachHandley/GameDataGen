import { GameDataGen } from '../src/GameDataGen.js';
import {
  globalImageGen,
  IMAGE_PROMPT_TEMPLATES,
  ImageStyle,
} from '../src/utils/ImageGenerationService.js';
import { globalKnowledgeGraph } from '../src/core/KnowledgeGraph.js';
import { z } from 'zod';

/**
 * Example: AI image generation for game content
 */

// Enhanced schema with image support
const ItemWithImageSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['weapon', 'armor', 'consumable']),
  rarity: z.enum(['common', 'rare', 'epic', 'legendary']),
  description: z.string(),
  // Image data
  generatedImage: z
    .object({
      url: z.string(),
      filepath: z.string().optional(),
      prompt: z.string(),
      style: z.string().optional(),
    })
    .optional(),
});

async function main() {
  console.log('🎨 AI Image Generation Example\n');

  // ============================================================
  // 1. Basic Image Generation
  // ============================================================

  console.log('🖼️  Basic image generation...\n');

  const result1 = await globalImageGen.generateImage({
    prompt: 'a glowing magical sword with blue flames, fantasy game item, high quality',
    model: 'dall-e-3',
    size: '1024x1024',
    quality: 'hd',
  });

  console.log('✓ Generated image:');
  console.log(`  URL: ${result1.images[0].url}`);
  console.log(`  Model: ${result1.model}`);
  console.log(`  Estimated cost: $${result1.totalCost?.toFixed(4)}`);
  if (result1.images[0].revisedPrompt) {
    console.log(`  Revised prompt: ${result1.images[0].revisedPrompt}`);
  }

  console.log();

  // ============================================================
  // 2. Generate Images for Game Entities
  // ============================================================

  console.log('⚔️  Generating images for game entities...\n');

  const gen = new GameDataGen({
    model: 'gpt-4o-mini',
    temperature: 0.8,
  });

  gen.registerSchema({
    name: 'ItemWithImage',
    schema: ItemWithImageSchema,
    description: 'Items with AI-generated images',
  });

  // Sample items (simulate generation)
  const sampleItems = [
    {
      id: 'sword_of_flames',
      name: 'Sword of Eternal Flames',
      type: 'weapon',
      rarity: 'legendary',
      description: 'A blade forged in dragon fire, eternally burning with crimson flames',
    },
    {
      id: 'frost_armor',
      name: 'Frostguard Plate Armor',
      type: 'armor',
      rarity: 'epic',
      description: 'Crystalline armor that emanates freezing aura, forged from glacier ice',
    },
    {
      id: 'phoenix_potion',
      name: 'Phoenix Rebirth Elixir',
      type: 'consumable',
      rarity: 'rare',
      description: 'Golden potion that glows with regenerative phoenix magic',
    },
  ];

  const imageStyles: ImageStyle[] = ['fantasy-realistic', 'painterly', 'pixel-art'];

  for (let i = 0; i < sampleItems.length; i++) {
    const item = sampleItems[i];
    const style = imageStyles[i];

    console.log(`Generating image for: ${item.name}`);
    console.log(`  Style: ${style}`);

    try {
      const imageResult = await globalImageGen.generateAndSave(
        {
          entityType: 'Item',
          entityData: item,
          style,
        },
        './output/images/items'
      );

      console.log(`  ✓ Saved to: ${imageResult.filepath}`);
      console.log(`  Prompt: ${imageResult.prompt}`);

      // Add image data to entity
      const itemWithImage = {
        ...item,
        generatedImage: {
          url: imageResult.url,
          filepath: imageResult.filepath,
          prompt: imageResult.prompt,
          style,
        },
      };

      gen.context.addEntity({
        id: item.id,
        type: 'ItemWithImage',
        data: itemWithImage,
        metadata: { generatedAt: new Date() },
      });

      // Track in knowledge graph
      globalKnowledgeGraph.addTriplet({
        subject: { type: 'ItemWithImage', id: item.id },
        predicate: 'has_generated_image',
        object: { type: 'Image', id: imageResult.filepath },
        metadata: {
          url: imageResult.url,
          prompt: imageResult.prompt,
          style,
          generatedAt: new Date().toISOString(),
        },
      });

      console.log();
    } catch (error) {
      console.error(`  ✗ Failed: ${error instanceof Error ? error.message : String(error)}`);
      console.log();
    }
  }

  // ============================================================
  // 3. Using Prompt Templates
  // ============================================================

  console.log('📝 Using prompt templates...\n');

  const templatedPrompts = {
    'Legendary Dragon Blade': IMAGE_PROMPT_TEMPLATES.legendaryWeapon(
      'Dragon Blade',
      'fire'
    ),
    'Adamantite Full Plate': IMAGE_PROMPT_TEMPLATES.epicArmor(
      'Full Plate',
      'adamantite'
    ),
    'Healing Potion': IMAGE_PROMPT_TEMPLATES.magicalPotion('red', 'healing'),
    'Ancient Red Dragon': IMAGE_PROMPT_TEMPLATES.dragonBoss(
      'ancient red',
      'volcanic mountain'
    ),
  };

  for (const [name, prompt] of Object.entries(templatedPrompts)) {
    console.log(`${name}:`);
    console.log(`  Prompt: ${prompt.substring(0, 80)}...`);
  }

  console.log();

  // Generate one example from template
  console.log('Generating from template: Legendary Dragon Blade\n');

  try {
    const templateResult = await globalImageGen.generateImage({
      prompt: templatedPrompts['Legendary Dragon Blade'],
      model: 'dall-e-3',
      size: '1024x1024',
      quality: 'hd',
    });

    const imageUrl = templateResult.images[0].url;
    await globalImageGen.downloadImage(
      imageUrl,
      './output/images/template_dragon_blade.png'
    );

    console.log('✓ Generated and saved to: ./output/images/template_dragon_blade.png');
    console.log(`  Cost: $${templateResult.totalCost?.toFixed(4)}`);
  } catch (error) {
    console.error(`✗ Failed: ${error instanceof Error ? error.message : String(error)}`);
  }

  console.log();

  // ============================================================
  // 4. Different Art Styles
  // ============================================================

  console.log('🎨 Generating in different art styles...\n');

  const styles: ImageStyle[] = [
    'pixel-art',
    'fantasy-realistic',
    'anime',
    'painterly',
    'comic-book',
  ];

  const baseItem = {
    name: 'Magic Staff',
    type: 'weapon',
    description: 'A mystical staff topped with a glowing crystal orb',
  };

  console.log('Generating "Magic Staff" in 5 different styles...');
  console.log('(This will take a minute and cost ~$0.20)\n');

  for (const style of styles) {
    console.log(`  ${style}... `);

    try {
      const styleResult = await globalImageGen.generateEntityImage({
        entityType: 'Item',
        entityData: baseItem,
        style,
      });

      const filename = `magic_staff_${style.replace(/-/g, '_')}.png`;
      await globalImageGen.downloadImage(
        styleResult.images[0].url,
        `./output/images/styles/${filename}`
      );

      console.log(`✓ Saved`);
    } catch (error) {
      console.log(`✗ Failed`);
    }
  }

  console.log();

  // ============================================================
  // 5. Character Portrait Generation
  // ============================================================

  console.log('👤 Generating character portraits...\n');

  const character = {
    name: 'Eldric the Wise',
    race: 'Elf',
    class: 'Wizard',
    appearance: {
      build: 'slim',
      hairColor: 'silver',
      eyeColor: 'amber',
      clothing: 'elegant blue robes with star patterns',
      distinguishingFeatures: 'long flowing beard, arcane tattoos on hands',
    },
    personality: 'wise and mysterious',
  };

  console.log(`Generating portrait for: ${character.name}`);

  try {
    const portraitResult = await globalImageGen.generateEntityImage({
      entityType: 'NPC',
      entityData: character,
      style: 'fantasy-realistic',
    });

    await globalImageGen.downloadImage(
      portraitResult.images[0].url,
      './output/images/characters/eldric_the_wise.png'
    );

    console.log('✓ Saved to: ./output/images/characters/eldric_the_wise.png');
    console.log(`  Prompt used: ${portraitResult.prompt}`);
  } catch (error) {
    console.error(`✗ Failed: ${error instanceof Error ? error.message : String(error)}`);
  }

  console.log();

  // ============================================================
  // 6. Environment/Zone Generation
  // ============================================================

  console.log('🏞️  Generating environment art...\n');

  const zone = {
    name: 'Shadowmoon Forest',
    biome: 'enchanted forest',
    environment: 'dense woodland',
    description: 'Dark mystical forest with glowing mushrooms and ethereal mist',
    climate: 'perpetual twilight',
  };

  console.log(`Generating environment: ${zone.name}`);

  try {
    const envResult = await globalImageGen.generateEntityImage({
      entityType: 'Zone',
      entityData: zone,
      style: 'painterly',
    });

    await globalImageGen.downloadImage(
      envResult.images[0].url,
      './output/images/environments/shadowmoon_forest.png'
    );

    console.log('✓ Saved to: ./output/images/environments/shadowmoon_forest.png');
    console.log(`  Prompt: ${envResult.prompt}`);
  } catch (error) {
    console.error(`✗ Failed: ${error instanceof Error ? error.message : String(error)}`);
  }

  console.log();

  // ============================================================
  // 7. Spell Effect Generation
  // ============================================================

  console.log('✨ Generating spell effects...\n');

  const spell = {
    name: 'Meteor Storm',
    school: 'fire',
    description: 'Summons a rain of flaming meteors from the sky',
  };

  console.log(`Generating spell effect: ${spell.name}`);

  try {
    const spellResult = await globalImageGen.generateEntityImage({
      entityType: 'Spell',
      entityData: spell,
      style: 'vivid',
      customPromptAdditions:
        'dramatic action shot, multiple meteors falling, explosion effects',
    });

    await globalImageGen.downloadImage(
      spellResult.images[0].url,
      './output/images/spells/meteor_storm.png'
    );

    console.log('✓ Saved to: ./output/images/spells/meteor_storm.png');
  } catch (error) {
    console.error(`✗ Failed: ${error instanceof Error ? error.message : String(error)}`);
  }

  console.log();

  // ============================================================
  // 8. Query Knowledge Graph for Images
  // ============================================================

  console.log('🔍 Querying knowledge graph for generated images...\n');

  const imageRelations = globalKnowledgeGraph.find({
    predicate: 'has_generated_image',
  });

  console.log(`Found ${imageRelations.length} entities with generated images:`);
  for (const rel of imageRelations) {
    const entity = gen.getEntity(rel.subject.type, rel.subject.id);
    console.log(`  - ${entity?.data.name}`);
    console.log(`    Style: ${rel.metadata?.style}`);
    console.log(`    File: ${rel.metadata?.url?.substring(0, 50)}...`);
  }

  console.log();

  // ============================================================
  // 9. Export Image Manifest
  // ============================================================

  console.log('📄 Generating image manifest...\n');

  const manifest = {
    generated: new Date().toISOString(),
    totalImages: imageRelations.length,
    images: imageRelations.map((rel) => {
      const entity = gen.getEntity(rel.subject.type, rel.subject.id);
      return {
        entityId: rel.subject.id,
        entityType: rel.subject.type,
        entityName: entity?.data.name,
        imageUrl: rel.metadata?.url,
        style: rel.metadata?.style,
        prompt: rel.metadata?.prompt,
        generatedAt: rel.metadata?.generatedAt,
      };
    }),
  };

  const fs = await import('fs/promises');
  await fs.writeFile(
    './output/images/manifest.json',
    JSON.stringify(manifest, null, 2)
  );

  console.log('✓ Saved manifest to: ./output/images/manifest.json');

  // ============================================================
  // 10. Cost Summary
  // ============================================================

  console.log('\n💰 Cost Summary:\n');

  console.log('Approximate costs (as of 2024):');
  console.log('  DALL-E 3 Standard 1024x1024: $0.040 per image');
  console.log('  DALL-E 3 HD 1024x1024: $0.080 per image');
  console.log('  DALL-E 3 HD 1792x1024: $0.120 per image');
  console.log();
  console.log(
    `Total images generated this session: ${imageRelations.length}`
  );
  console.log(`Estimated total cost: $${(imageRelations.length * 0.08).toFixed(2)}`);

  console.log();

  // ============================================================
  // 11. Usage Examples
  // ============================================================

  console.log('💡 Usage Examples:\n');

  console.log('```typescript');
  console.log('// 1. Generate item image');
  console.log('const result = await globalImageGen.generateEntityImage({');
  console.log('  entityType: "Item",');
  console.log('  entityData: { name: "Sword", description: "..." },');
  console.log('  style: "fantasy-realistic"');
  console.log('});');
  console.log('');
  console.log('// 2. Generate and save');
  console.log('await globalImageGen.generateAndSave(');
  console.log('  { entityType: "Item", entityData: item },');
  console.log('  "./images"');
  console.log(');');
  console.log('');
  console.log('// 3. Use template');
  console.log('const prompt = IMAGE_PROMPT_TEMPLATES.legendaryWeapon(');
  console.log('  "Excalibur", "holy"');
  console.log(');');
  console.log('await globalImageGen.generateImage({ prompt });');
  console.log('```');

  console.log('\n✅ Image generation complete!\n');
}

main().catch(console.error);
