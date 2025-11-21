import { GameDataGen } from '../src/GameDataGen.js';
import {
  globalImageGen,
  ImageStyle,
} from '../src/utils/ImageGenerationService.js';
import { globalPromptBuilder } from '../src/utils/PromptBuilder.js';
import {
  globalQualityChecker,
  generateWithQualityControl,
} from '../src/utils/ImageQualityChecker.js';
import { z } from 'zod';

/**
 * Example: Image Quality Control Workflow
 *
 * Demonstrates:
 * 1. Optimized prompt building for different AI models
 * 2. Automatic quality checking with GPT-4o-mini vision
 * 3. Auto-retry on quality issues
 * 4. Manual review workflow
 */

async function main() {
  console.log('🎨 Image Quality Control Workflow\n');

  // ============================================================
  // 1. Generate with Automatic Quality Control
  // ============================================================

  console.log('📋 Example 1: Auto-retry with quality control\n');

  const legendaryWeapon = {
    id: 'sword_001',
    name: 'Flamebringer',
    type: 'sword',
    rarity: 'legendary',
    description: 'A blade forged in dragon fire, eternally burning with crimson flames',
    material: 'mithril',
    enchantment: 'fire',
  };

  console.log(`Generating image for: ${legendaryWeapon.name}`);
  console.log('Quality control enabled with auto-retry...\n');

  try {
    const result = await globalImageGen.generateAndSave(
      {
        entityType: 'Item',
        entityData: legendaryWeapon,
        style: 'fantasy-realistic',
        enableQualityCheck: true,
        qualityCheckOptions: {
          strictMode: false, // Normal quality standards
          checkForText: true, // Check for unwanted text artifacts
        },
        qualityControlOptions: {
          maxRetries: 3, // Try up to 3 times
          autoApprove: false, // Require manual review even if passed
        },
      },
      './output/images/qc-examples'
    );

    console.log('✅ Generation complete!\n');
    console.log(`📁 Saved to: ${result.filepath}`);
    console.log(`🔗 URL: ${result.url.substring(0, 60)}...`);
    console.log(`📝 Prompt: ${result.prompt.substring(0, 100)}...`);

    if (result.qualityCheck) {
      console.log('\n📊 Quality Check Results:');
      console.log(globalImageGen.formatQualityResult(result.qualityCheck));
      console.log(`\n🔄 Generation attempts: ${result.attempts}`);
    }
  } catch (error) {
    console.error('❌ Failed:', error instanceof Error ? error.message : String(error));
  }

  console.log('\n' + '='.repeat(60) + '\n');

  // ============================================================
  // 2. Manual Quality Check on Existing Image
  // ============================================================

  console.log('📋 Example 2: Manual quality check\n');

  // Generate an image first
  const magicStaff = {
    id: 'staff_001',
    name: 'Staff of Arcane Mastery',
    type: 'staff',
    rarity: 'epic',
    description: 'Ancient staff topped with a glowing crystal orb of pure arcane energy',
  };

  console.log(`Generating: ${magicStaff.name}`);

  const staffResult = await globalImageGen.generateEntityImage({
    entityType: 'Item',
    entityData: magicStaff,
    style: 'fantasy-realistic',
  });

  console.log('✓ Image generated\n');

  // Now check its quality
  console.log('🔍 Running quality check...\n');

  const qualityCheck = await globalImageGen.checkImageQuality(
    staffResult.images[0].url,
    'Item',
    magicStaff.description,
    { strictMode: false }
  );

  console.log(globalImageGen.formatQualityResult(qualityCheck));

  console.log('\n' + '='.repeat(60) + '\n');

  // ============================================================
  // 3. Strict Mode Quality Control
  // ============================================================

  console.log('📋 Example 3: Strict mode quality control\n');

  const characterData = {
    id: 'npc_001',
    name: 'Archmage Elara',
    race: 'High Elf',
    class: 'Wizard',
    appearance: {
      build: 'slim',
      hairColor: 'silver-white',
      eyeColor: 'violet',
      height: 6.2,
      clothing: 'elaborate purple robes with golden embroidery and arcane runes',
      distinguishingFeatures: 'glowing arcane tattoos on arms, staff with floating orb',
    },
    personality: 'wise and mysterious',
  };

  console.log(`Generating character portrait: ${characterData.name}`);
  console.log('Strict mode enabled - more critical quality standards\n');

  try {
    const strictResult = await globalImageGen.generateAndSave(
      {
        entityType: 'NPC',
        entityData: characterData,
        style: 'fantasy-realistic',
        enableQualityCheck: true,
        qualityCheckOptions: {
          strictMode: true, // Stricter standards
          checkForText: true,
        },
        qualityControlOptions: {
          maxRetries: 3,
          autoApprove: false,
        },
      },
      './output/images/qc-examples'
    );

    console.log('✅ Character portrait generated!\n');
    console.log(`📁 Saved to: ${strictResult.filepath}`);

    if (strictResult.qualityCheck) {
      console.log('\n📊 Quality Check Results (Strict Mode):');
      console.log(globalImageGen.formatQualityResult(strictResult.qualityCheck));
      console.log(`\n🔄 Attempts needed: ${strictResult.attempts}`);
    }
  } catch (error) {
    console.error('❌ Failed:', error instanceof Error ? error.message : String(error));
  }

  console.log('\n' + '='.repeat(60) + '\n');

  // ============================================================
  // 4. Custom Quality Check Callback
  // ============================================================

  console.log('📋 Example 4: Custom quality check workflow\n');

  const dragonBoss = {
    id: 'boss_001',
    name: 'Ignis the Eternal Flame',
    type: 'Ancient Dragon',
    level: 100,
    isBoss: true,
    description: 'Massive red dragon with scales like molten lava, breathing intense flames',
  };

  console.log(`Generating boss image: ${dragonBoss.name}`);
  console.log('Using custom quality check callback...\n');

  let checkCount = 0;

  try {
    const customResult = await globalImageGen.generateAndSave(
      {
        entityType: 'Enemy',
        entityData: dragonBoss,
        style: 'fantasy-realistic',
        enableQualityCheck: true,
        qualityControlOptions: {
          maxRetries: 3,
          autoApprove: false,
          onQualityCheck: async (result) => {
            checkCount++;
            console.log(`\n🔍 Quality check #${checkCount}:`);
            console.log(globalImageGen.formatQualityResult(result));

            // Custom logic: approve if score >= 75 and no severe issues
            const hasSevereIssues = result.issues.some(i => i.severity === 'severe');

            if (result.score >= 75 && !hasSevereIssues) {
              console.log('\n✅ Manually approved (score >= 75, no severe issues)');
              return 'approve';
            } else if (result.score < 50) {
              console.log('\n🔄 Regenerating (score too low)');
              return 'regenerate';
            } else {
              console.log('\n⏸️  Would require manual review in production');
              return 'approve'; // Auto-approve for demo
            }
          },
        },
      },
      './output/images/qc-examples'
    );

    console.log('\n✅ Boss image generated!\n');
    console.log(`📁 Saved to: ${customResult.filepath}`);
    console.log(`🔄 Total quality checks performed: ${checkCount}`);
  } catch (error) {
    console.error('❌ Failed:', error instanceof Error ? error.message : String(error));
  }

  console.log('\n' + '='.repeat(60) + '\n');

  // ============================================================
  // 5. Optimized Prompts for Different Models
  // ============================================================

  console.log('📋 Example 5: Model-specific prompt optimization\n');

  const spellData = {
    name: 'Meteor Storm',
    school: 'fire',
    description: 'Summons a devastating rain of flaming meteors from the sky',
  };

  // DALL-E 3 (structured prompt)
  const dallePrompt = globalPromptBuilder.build({
    model: 'dall-e-3',
    entityType: 'Spell',
    entityData: spellData,
    style: 'fantasy-realistic',
    lighting: 'dramatic lighting',
    cameraAngle: 'low-angle',
  });

  console.log('🎯 DALL-E 3 Prompt (structured):');
  console.log(dallePrompt);
  console.log();

  // Gemini Imagen (narrative prompt)
  const geminiPrompt = globalPromptBuilder.build({
    model: 'gemini-imagen-3',
    entityType: 'Spell',
    entityData: spellData,
    style: 'fantasy-realistic',
    lighting: 'dramatic lighting',
    cameraAngle: 'low-angle',
  });

  console.log('🎯 Gemini Imagen Prompt (narrative):');
  console.log(geminiPrompt);
  console.log();

  console.log('Note: Notice how DALL-E gets structured sections (SUBJECT, COMPOSITION, etc.)');
  console.log('      while Gemini gets a flowing narrative description.');

  console.log('\n' + '='.repeat(60) + '\n');

  // ============================================================
  // 6. Batch Quality Check
  // ============================================================

  console.log('📋 Example 6: Batch quality checking\n');

  const itemBatch = [
    {
      id: 'potion_001',
      name: 'Greater Healing Potion',
      type: 'consumable',
      description: 'Glowing red potion in ornate glass bottle',
    },
    {
      id: 'armor_001',
      name: 'Dragonscale Chestplate',
      type: 'armor',
      description: 'Heavy armor crafted from black dragon scales',
    },
    {
      id: 'ring_001',
      name: 'Ring of Protection',
      type: 'accessory',
      description: 'Golden ring with embedded sapphire, emanating magical barrier',
    },
  ];

  console.log(`Generating ${itemBatch.length} items with quality control...\n`);

  const batchResults = [];

  for (let i = 0; i < itemBatch.length; i++) {
    const item = itemBatch[i];
    console.log(`[${i + 1}/${itemBatch.length}] ${item.name}`);

    try {
      // Generate without QC for speed in this example
      const result = await globalImageGen.generateEntityImage({
        entityType: 'Item',
        entityData: item,
        style: 'fantasy-realistic',
      });

      // Then check quality
      const qc = await globalQualityChecker.checkImage(result.images[0].url, {
        entityType: 'Item',
        expectedContent: item.description,
        strictMode: false,
      });

      batchResults.push({
        item: item.name,
        score: qc.score,
        passed: qc.passed,
        recommendation: qc.recommendation,
      });

      console.log(`  Score: ${qc.score}/100 - ${qc.passed ? '✅ PASSED' : '❌ FAILED'}`);
    } catch (error) {
      console.log(`  ❌ Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  console.log('\n📊 Batch Results Summary:');
  console.log('┌─────────────────────────────────┬───────┬────────┬────────────────┐');
  console.log('│ Item                            │ Score │ Passed │ Recommendation │');
  console.log('├─────────────────────────────────┼───────┼────────┼────────────────┤');

  for (const result of batchResults) {
    const itemPadded = result.item.padEnd(31);
    const scorePadded = String(result.score).padEnd(5);
    const passedEmoji = result.passed ? '✅' : '❌';
    const recPadded = result.recommendation.padEnd(14);

    console.log(`│ ${itemPadded} │ ${scorePadded} │ ${passedEmoji}    │ ${recPadded} │`);
  }

  console.log('└─────────────────────────────────┴───────┴────────┴────────────────┘');

  const avgScore = batchResults.reduce((sum, r) => sum + r.score, 0) / batchResults.length;
  const passRate = (batchResults.filter(r => r.passed).length / batchResults.length) * 100;

  console.log(`\nAverage Quality Score: ${avgScore.toFixed(1)}/100`);
  console.log(`Pass Rate: ${passRate.toFixed(0)}%`);

  console.log('\n' + '='.repeat(60) + '\n');

  // ============================================================
  // Summary
  // ============================================================

  console.log('📝 Quality Control Summary\n');

  console.log('✅ Quality Control Features:');
  console.log('  • GPT-4o-mini vision for fast, cheap quality checking');
  console.log('  • Detects AI artifacts, anatomy issues, unwanted text');
  console.log('  • Auto-retry with configurable max attempts');
  console.log('  • Custom quality check callbacks for manual review');
  console.log('  • Strict mode for higher quality standards');
  console.log('  • Batch quality checking support\n');

  console.log('✅ Prompt Optimization:');
  console.log('  • Model-specific prompts (DALL-E vs Gemini)');
  console.log('  • DALL-E: Structured format with sections');
  console.log('  • Gemini: Narrative, story-like descriptions');
  console.log('  • Photographer language (camera angles, lenses, lighting)');
  console.log('  • Explicit text artifact avoidance\n');

  console.log('💰 Cost Efficiency:');
  console.log('  • GPT-4o-mini vision: ~$0.001 per check');
  console.log('  • DALL-E 3 HD 1024x1024: $0.080 per image');
  console.log('  • With 3 retries: ~$0.243 total worst case');
  console.log('  • Most images pass on first attempt\n');

  console.log('🔧 Integration:');
  console.log('```typescript');
  console.log('// Enable quality control in any generation');
  console.log('const result = await globalImageGen.generateAndSave({');
  console.log('  entityType: "Item",');
  console.log('  entityData: myItem,');
  console.log('  enableQualityCheck: true,');
  console.log('  qualityCheckOptions: { strictMode: false },');
  console.log('  qualityControlOptions: { maxRetries: 3 }');
  console.log('}, "./output");');
  console.log('```\n');

  console.log('✅ Quality control workflow complete!\n');
}

main().catch(console.error);
