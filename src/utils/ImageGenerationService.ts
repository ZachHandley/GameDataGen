/**
 * Image generation service using OpenAI DALL-E
 * Generates custom images for game content (items, characters, scenes, etc.)
 */

import OpenAI from 'openai';
import { PromptBuilder, ImageModel } from './PromptBuilder.js';
import {
  ImageQualityChecker,
  QualityCheckOptions,
  QualityCheckResult,
  generateWithQualityControl,
  GenerateWithQCOptions,
} from './ImageQualityChecker.js';

export interface ImageGenerationRequest {
  prompt: string;
  model?: 'dall-e-2' | 'dall-e-3';
  size?: '256x256' | '512x512' | '1024x1024' | '1792x1024' | '1024x1792';
  quality?: 'standard' | 'hd';
  style?: 'natural' | 'vivid';
  n?: number; // Number of images (1-10 for DALL-E 2, only 1 for DALL-E 3)
}

export interface GeneratedImage {
  url: string;
  revisedPrompt?: string; // DALL-E 3 returns revised prompt
  b64_json?: string; // Base64 encoded image
}

export interface ImageGenerationResult {
  images: GeneratedImage[];
  prompt: string;
  model: string;
  totalCost?: number; // Estimated cost in USD
}

export interface EntityImageRequest {
  entityType: string;
  entityData: any;
  style?: ImageStyle;
  customPromptAdditions?: string;
  // Quality control options
  enableQualityCheck?: boolean;
  qualityCheckOptions?: Partial<QualityCheckOptions>;
  qualityControlOptions?: GenerateWithQCOptions;
}

export type ImageStyle =
  | 'pixel-art'
  | 'fantasy-realistic'
  | 'anime'
  | 'painterly'
  | 'sketch'
  | 'comic-book'
  | 'low-poly-3d'
  | 'isometric'
  | 'oil-painting'
  | 'watercolor';

/**
 * Image generation service
 */
export class ImageGenerationService {
  private client: OpenAI;
  private cache: Map<string, GeneratedImage[]> = new Map();
  private defaultModel: 'dall-e-2' | 'dall-e-3' = 'dall-e-3';
  private promptBuilder: PromptBuilder;
  private qualityChecker: ImageQualityChecker;

  constructor(apiKey?: string) {
    this.client = new OpenAI({
      apiKey: apiKey || process.env.OPENAI_API_KEY,
    });
    this.promptBuilder = new PromptBuilder();
    this.qualityChecker = new ImageQualityChecker(apiKey);
  }

  /**
   * Generate images from a prompt
   */
  async generateImage(
    request: ImageGenerationRequest
  ): Promise<ImageGenerationResult> {
    const {
      prompt,
      model = this.defaultModel,
      size = '1024x1024',
      quality = 'standard',
      style = 'vivid',
      n = 1,
    } = request;

    // Validate n for DALL-E 3
    if (model === 'dall-e-3' && n > 1) {
      throw new Error('DALL-E 3 only supports n=1');
    }

    // Check cache
    const cacheKey = `${model}:${size}:${quality}:${prompt}`;
    if (this.cache.has(cacheKey)) {
      return {
        images: this.cache.get(cacheKey)!,
        prompt,
        model,
      };
    }

    try {
      const response = await this.client.images.generate({
        model,
        prompt,
        n,
        size: size as any,
        quality: model === 'dall-e-3' ? quality : undefined,
        style: model === 'dall-e-3' ? style : undefined,
        response_format: 'url',
      });

      if (!response.data || response.data.length === 0) {
        throw new Error('No images generated');
      }

      const images: GeneratedImage[] = response.data.map((img) => ({
        url: img.url!,
        revisedPrompt: (img as any).revised_prompt,
      }));

      // Cache the result
      this.cache.set(cacheKey, images);

      // Calculate estimated cost
      const totalCost = this.estimateCost(model, size, quality, n);

      return {
        images,
        prompt,
        model,
        totalCost,
      };
    } catch (error) {
      throw new Error(
        `Failed to generate image: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Generate image for a game entity
   */
  async generateEntityImage(
    request: EntityImageRequest
  ): Promise<ImageGenerationResult> {
    // Use PromptBuilder for better prompts
    const prompt = this.promptBuilder.build({
      model: 'dall-e-3' as ImageModel,
      entityType: request.entityType,
      entityData: request.entityData,
      style: request.style,
      customAdditions: request.customPromptAdditions,
      avoidTextArtifacts: true,
    });

    return this.generateImage({
      prompt,
      model: 'dall-e-3',
      size: this.getSizeForEntityType(request.entityType),
      quality: 'hd',
      style: 'vivid',
    });
  }

  /**
   * Build prompt for entity
   */
  private buildEntityPrompt(
    entityType: string,
    entityData: any,
    style?: ImageStyle,
    customAdditions?: string
  ): string {
    const type = entityType.toLowerCase();
    const parts: string[] = [];

    // Add style prefix
    if (style) {
      parts.push(this.getStylePrefix(style));
    }

    // Add entity-specific description
    if (type.includes('item') || type.includes('weapon') || type.includes('armor')) {
      parts.push(this.buildItemPrompt(entityData));
    } else if (type.includes('npc') || type.includes('character')) {
      parts.push(this.buildCharacterPrompt(entityData));
    } else if (type.includes('enemy') || type.includes('boss')) {
      parts.push(this.buildEnemyPrompt(entityData));
    } else if (type.includes('zone') || type.includes('environment')) {
      parts.push(this.buildEnvironmentPrompt(entityData));
    } else if (type.includes('spell') || type.includes('magic')) {
      parts.push(this.buildSpellPrompt(entityData));
    } else {
      // Generic description
      parts.push(entityData.description || entityData.name || 'fantasy game asset');
    }

    // Add custom additions
    if (customAdditions) {
      parts.push(customAdditions);
    }

    // Add quality suffix
    parts.push('high quality, detailed, professional game art');

    return parts.join(', ');
  }

  /**
   * Build prompt for items/weapons/armor
   */
  private buildItemPrompt(data: any): string {
    const parts: string[] = [];

    if (data.name) parts.push(data.name);
    if (data.type) parts.push(data.type);
    if (data.rarity) parts.push(`${data.rarity} rarity`);
    if (data.description) parts.push(data.description);

    // Add material/visual details if available
    if (data.material) parts.push(`made of ${data.material}`);
    if (data.enchantment) parts.push(`glowing with ${data.enchantment} magic`);

    parts.push('on white background, game item icon, centered');

    return parts.join(', ');
  }

  /**
   * Build prompt for characters/NPCs
   */
  private buildCharacterPrompt(data: any): string {
    const parts: string[] = [];

    if (data.name) parts.push(data.name);
    if (data.race) parts.push(data.race);
    if (data.class) parts.push(data.class);

    // Appearance details
    if (data.appearance) {
      const app = data.appearance;
      if (app.build) parts.push(`${app.build} build`);
      if (app.hairColor) parts.push(`${app.hairColor} hair`);
      if (app.eyeColor) parts.push(`${app.eyeColor} eyes`);
      if (app.clothing) parts.push(`wearing ${app.clothing}`);
      if (app.distinguishingFeatures) parts.push(app.distinguishingFeatures);
    }

    if (data.personality) parts.push(data.personality);
    if (data.description) parts.push(data.description);

    parts.push('character portrait, fantasy RPG style');

    return parts.join(', ');
  }

  /**
   * Build prompt for enemies/bosses
   */
  private buildEnemyPrompt(data: any): string {
    const parts: string[] = [];

    if (data.name) parts.push(data.name);
    if (data.type) parts.push(data.type);
    if (data.description) parts.push(data.description);

    // Size/power indicators
    if (data.level > 50) parts.push('powerful, imposing');
    if (data.isBoss) parts.push('boss monster, epic');

    parts.push('fantasy creature, menacing, detailed');

    return parts.join(', ');
  }

  /**
   * Build prompt for environments/zones
   */
  private buildEnvironmentPrompt(data: any): string {
    const parts: string[] = [];

    if (data.name) parts.push(data.name);
    if (data.biome) parts.push(data.biome);
    if (data.environment) parts.push(data.environment);
    if (data.description) parts.push(data.description);

    // Atmosphere
    if (data.climate) parts.push(data.climate);
    if (data.lore) parts.push('atmospheric, mysterious');

    parts.push('fantasy landscape, game environment, wide shot');

    return parts.join(', ');
  }

  /**
   * Build prompt for spells/magic
   */
  private buildSpellPrompt(data: any): string {
    const parts: string[] = [];

    if (data.name) parts.push(data.name);
    if (data.school) parts.push(`${data.school} magic`);
    if (data.description) parts.push(data.description);

    // Visual effects
    if (data.school === 'fire') parts.push('flames, burning, orange glow');
    if (data.school === 'ice') parts.push('frost, ice crystals, blue glow');
    if (data.school === 'nature') parts.push('vines, leaves, green energy');
    if (data.school === 'arcane') parts.push('purple energy, mystical runes');

    parts.push('spell effect, magical energy, glowing');

    return parts.join(', ');
  }

  /**
   * Get style prefix for prompt
   */
  private getStylePrefix(style: ImageStyle): string {
    switch (style) {
      case 'pixel-art':
        return 'pixel art style, retro game graphics, 16-bit';
      case 'fantasy-realistic':
        return 'realistic fantasy art, detailed, high quality render';
      case 'anime':
        return 'anime art style, vibrant colors, manga inspired';
      case 'painterly':
        return 'painterly style, artistic, brushstrokes visible';
      case 'sketch':
        return 'pencil sketch, hand-drawn, monochrome';
      case 'comic-book':
        return 'comic book art style, bold lines, dynamic';
      case 'low-poly-3d':
        return 'low poly 3D art, geometric, stylized';
      case 'isometric':
        return 'isometric view, game asset, top-down perspective';
      case 'oil-painting':
        return 'oil painting style, classical art, rich colors';
      case 'watercolor':
        return 'watercolor painting, soft edges, translucent';
      default:
        return '';
    }
  }

  /**
   * Get appropriate size for entity type
   */
  private getSizeForEntityType(entityType: string): '1024x1024' | '1792x1024' | '1024x1792' {
    const type = entityType.toLowerCase();

    if (type.includes('environment') || type.includes('zone') || type.includes('landscape')) {
      return '1792x1024'; // Wide landscape
    }

    if (type.includes('character') || type.includes('npc') || type.includes('enemy')) {
      return '1024x1792'; // Tall portrait
    }

    return '1024x1024'; // Square for items/icons
  }

  /**
   * Download image to file
   */
  async downloadImage(
    url: string,
    filepath: string
  ): Promise<void> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to download image: ${response.statusText}`);
    }

    const buffer = await response.arrayBuffer();
    const fs = await import('fs/promises');

    // Create directory if needed
    const path = await import('path');
    const dir = path.dirname(filepath);
    await fs.mkdir(dir, { recursive: true });

    await fs.writeFile(filepath, Buffer.from(buffer));
  }

  /**
   * Generate image with quality control
   */
  async generateEntityImageWithQC(
    request: EntityImageRequest
  ): Promise<{
    result: ImageGenerationResult;
    qualityCheck: QualityCheckResult;
    attempts: number;
  }> {
    const generateFn = async () => {
      const result = await this.generateEntityImage(request);
      return {
        url: result.images[0].url,
        prompt: result.prompt,
      };
    };

    const checkOptions: QualityCheckOptions = {
      entityType: request.entityType,
      expectedContent: request.entityData.description || request.entityData.name || 'game content',
      strictMode: request.qualityCheckOptions?.strictMode ?? false,
      checkForText: request.qualityCheckOptions?.checkForText ?? true,
    };

    const qcOptions: GenerateWithQCOptions = {
      maxRetries: request.qualityControlOptions?.maxRetries ?? 3,
      autoApprove: request.qualityControlOptions?.autoApprove ?? false,
      onQualityCheck: request.qualityControlOptions?.onQualityCheck,
    };

    const { url, prompt, qualityCheck, attempts } = await generateWithQualityControl(
      generateFn,
      checkOptions,
      qcOptions
    );

    // Get the full result
    const result = await this.generateImage({
      prompt,
      model: 'dall-e-3',
      size: this.getSizeForEntityType(request.entityType),
      quality: 'hd',
      style: 'vivid',
    });

    return {
      result: {
        images: [{ url }],
        prompt,
        model: 'dall-e-3',
      },
      qualityCheck,
      attempts,
    };
  }

  /**
   * Generate and save image for entity
   */
  async generateAndSave(
    request: EntityImageRequest,
    outputDir: string = './output/images'
  ): Promise<{
    filepath: string;
    url: string;
    prompt: string;
    qualityCheck?: QualityCheckResult;
    attempts?: number;
  }> {
    let result: ImageGenerationResult;
    let qualityCheck: QualityCheckResult | undefined;
    let attempts: number | undefined;

    // Use quality control if enabled
    if (request.enableQualityCheck) {
      const qcResult = await this.generateEntityImageWithQC(request);
      result = qcResult.result;
      qualityCheck = qcResult.qualityCheck;
      attempts = qcResult.attempts;
    } else {
      result = await this.generateEntityImage(request);
    }

    const image = result.images[0];

    const fs = await import('fs/promises');
    await fs.mkdir(outputDir, { recursive: true });

    // Generate filename
    const entityName = request.entityData.name || request.entityData.id || 'entity';
    const sanitized = entityName.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    const filename = `${request.entityType}_${sanitized}.png`;
    const filepath = `${outputDir}/${filename}`;

    // Download the image
    await this.downloadImage(image.url, filepath);

    return {
      filepath,
      url: image.url,
      prompt: result.prompt,
      qualityCheck,
      attempts,
    };
  }

  /**
   * Estimate cost in USD
   */
  private estimateCost(
    model: string,
    size: string,
    quality: string,
    n: number
  ): number {
    // DALL-E 3 pricing (as of 2024)
    if (model === 'dall-e-3') {
      if (quality === 'hd') {
        if (size === '1024x1024') return 0.08 * n;
        if (size === '1792x1024' || size === '1024x1792') return 0.12 * n;
      } else {
        if (size === '1024x1024') return 0.04 * n;
        if (size === '1792x1024' || size === '1024x1792') return 0.08 * n;
      }
    }

    // DALL-E 2 pricing
    if (model === 'dall-e-2') {
      if (size === '1024x1024') return 0.02 * n;
      if (size === '512x512') return 0.018 * n;
      if (size === '256x256') return 0.016 * n;
    }

    return 0.04 * n; // Default estimate
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Get cache stats
   */
  getCacheStats(): { size: number; prompts: string[] } {
    return {
      size: this.cache.size,
      prompts: Array.from(this.cache.keys()),
    };
  }

  /**
   * Quick quality check on an existing image URL
   */
  async checkImageQuality(
    imageUrl: string,
    entityType: string,
    expectedContent: string,
    options?: Partial<QualityCheckOptions>
  ): Promise<QualityCheckResult> {
    return this.qualityChecker.checkImage(imageUrl, {
      entityType,
      expectedContent,
      strictMode: options?.strictMode ?? false,
      checkForText: options?.checkForText ?? true,
    });
  }

  /**
   * Format quality check result for display
   */
  formatQualityResult(result: QualityCheckResult): string {
    return this.qualityChecker.formatResult(result);
  }
}

/**
 * Prompt templates for common game content
 */
export const IMAGE_PROMPT_TEMPLATES = {
  legendaryWeapon: (name: string, element: string) =>
    `${name}, legendary ${element} weapon, glowing with ${element} energy, ornate design, floating on mystical background, game item art, fantasy RPG, ultra detailed`,

  epicArmor: (name: string, material: string) =>
    `${name}, epic ${material} armor set, intricate engravings, metallic sheen, on stand with dramatic lighting, game equipment art, fantasy style, high quality`,

  magicalPotion: (color: string, effect: string) =>
    `magical potion bottle, ${color} liquid, glowing with ${effect} magic, ornate glass container, mystical particles, game item icon, white background, detailed`,

  dragonBoss: (dragonType: string, environment: string) =>
    `fearsome ${dragonType} dragon, massive wings spread, breathing elemental energy, in ${environment} setting, boss monster art, epic fantasy, detailed scales`,

  enchantedForest: (timeOfDay: string, mystical: boolean) =>
    `enchanted forest, ${timeOfDay} lighting, ${mystical ? 'magical glow, floating wisps,' : ''} ancient trees, fantasy game environment, atmospheric, detailed vegetation`,

  dungeonEntrance: (theme: string, danger: string) =>
    `${theme} dungeon entrance, ominous ${danger}, stone architecture, torch lighting, fantasy game location, atmospheric, mysterious`,

  treasureChest: (rarity: string, contents: string) =>
    `${rarity} treasure chest, ${contents} visible inside, glowing loot, ornate design, game asset, fantasy style, detailed`,
};

// Global image generation service
export const globalImageGen = new ImageGenerationService();
