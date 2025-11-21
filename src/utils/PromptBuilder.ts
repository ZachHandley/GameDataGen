/**
 * Improved prompt builder following best practices for different AI models
 *
 * Key principles:
 * - DALL-E 3: Detail-sensitive, fantasy-friendly, needs explicit structure
 * - Gemini Imagen: Narrative descriptions, photorealistic, conversational
 * - Both: Avoid text artifacts, use photographer language
 */

export type ImageModel = 'dall-e-2' | 'dall-e-3' | 'gemini-imagen-3';

export interface PromptBuilderOptions {
  model: ImageModel;
  entityType: string;
  entityData: any;
  style?: string;
  customAdditions?: string;

  // Advanced options
  avoidTextArtifacts?: boolean;  // Default: true
  photorealisticMode?: boolean;
  cameraAngle?: string;  // 'low-angle', 'wide-angle', 'macro', 'Dutch angle'
  lensType?: string;     // '85mm portrait', '24mm wide', 'macro lens'
  lighting?: string;     // 'dramatic lighting', 'soft diffused', 'golden hour'
}

/**
 * Build optimized prompts based on model and content type
 */
export class PromptBuilder {
  /**
   * Build a narrative prompt (best for Gemini)
   */
  buildNarrative(options: PromptBuilderOptions): string {
    const parts: string[] = [];

    // Start with a scene description
    parts.push(this.buildSceneDescription(options));

    // Add composition details
    if (options.cameraAngle || options.lensType) {
      parts.push(this.buildCameraDetails(options));
    }

    // Add lighting
    if (options.lighting) {
      parts.push(`The scene is illuminated with ${options.lighting}`);
    }

    // Add style as narrative
    if (options.style) {
      parts.push(this.getStyleNarrative(options.style));
    }

    // Avoid text artifacts
    if (options.avoidTextArtifacts !== false) {
      parts.push('Make sure no text or writing appears in the image.');
    }

    // Custom additions
    if (options.customAdditions) {
      parts.push(options.customAdditions);
    }

    // Quality suffix
    parts.push('The image should be high quality, detailed, and free of visual artifacts.');

    return parts.join(' ');
  }

  /**
   * Build a structured prompt (best for DALL-E 3)
   */
  buildStructured(options: PromptBuilderOptions): string {
    const sections: string[] = [];

    // Subject
    sections.push(`SUBJECT: ${this.getSubject(options)}`);

    // Composition
    sections.push(`COMPOSITION: ${this.getComposition(options)}`);

    // Action (if applicable)
    const action = this.getAction(options);
    if (action) {
      sections.push(`ACTION: ${action}`);
    }

    // Location/Setting
    sections.push(`SETTING: ${this.getSetting(options)}`);

    // Style
    if (options.style) {
      sections.push(`STYLE: ${options.style}`);
    }

    // Camera/Technical
    if (options.photorealisticMode || options.cameraAngle || options.lensType) {
      const camera = this.buildCameraDetails(options);
      sections.push(`TECHNICAL: ${camera}`);
    }

    // Lighting
    if (options.lighting) {
      sections.push(`LIGHTING: ${options.lighting}`);
    }

    // Quality & Constraints
    const constraints = [];
    if (options.avoidTextArtifacts !== false) {
      constraints.push('no text');
    }
    constraints.push('no visual artifacts');
    constraints.push('high quality');
    constraints.push('detailed');

    sections.push(`CONSTRAINTS: ${constraints.join(', ')}`);

    // Custom
    if (options.customAdditions) {
      sections.push(`ADDITIONAL: ${options.customAdditions}`);
    }

    return sections.join(', ');
  }

  /**
   * Build scene description (narrative style)
   */
  private buildSceneDescription(options: PromptBuilderOptions): string {
    const { entityType, entityData } = options;
    const type = entityType.toLowerCase();

    if (type.includes('item') || type.includes('weapon') || type.includes('armor')) {
      return this.buildItemScene(entityData);
    } else if (type.includes('character') || type.includes('npc')) {
      return this.buildCharacterScene(entityData);
    } else if (type.includes('enemy') || type.includes('boss')) {
      return this.buildEnemyScene(entityData);
    } else if (type.includes('zone') || type.includes('environment')) {
      return this.buildEnvironmentScene(entityData);
    } else if (type.includes('spell') || type.includes('magic')) {
      return this.buildSpellScene(entityData);
    }

    return `A scene depicting ${entityData.name || entityData.description || 'a fantasy game element'}.`;
  }

  /**
   * Build item scene (narrative)
   */
  private buildItemScene(data: any): string {
    const parts: string[] = [];

    if (data.name) {
      parts.push(`A ${data.rarity || ''} ${data.type || 'item'} known as the ${data.name}`);
    }

    if (data.description) {
      parts.push(data.description);
    }

    // Material details
    if (data.material) {
      parts.push(`crafted from ${data.material}`);
    }

    // Visual details
    if (data.enchantment || data.rarity === 'legendary' || data.rarity === 'epic') {
      parts.push('emanating a mystical glow');
    }

    // Context
    parts.push('displayed prominently against a clean background, centered and in focus');

    return parts.join(', ') + '.';
  }

  /**
   * Build character scene (narrative)
   */
  private buildCharacterScene(data: any): string {
    const parts: string[] = [];

    // Introduction
    if (data.name && data.race && data.class) {
      parts.push(`${data.name}, a ${data.race} ${data.class}`);
    }

    // Appearance
    if (data.appearance) {
      const app = data.appearance;
      const details: string[] = [];

      if (app.build) details.push(`${app.build} build`);
      if (app.hairColor) details.push(`${app.hairColor} hair`);
      if (app.eyeColor) details.push(`${app.eyeColor} eyes`);

      if (details.length > 0) {
        parts.push(`with ${details.join(', ')}`);
      }

      if (app.clothing) {
        parts.push(`wearing ${app.clothing}`);
      }

      if (app.distinguishingFeatures) {
        parts.push(`featuring ${app.distinguishingFeatures}`);
      }
    }

    // Personality/Mood
    if (data.personality) {
      parts.push(`The character has a ${data.personality} demeanor`);
    }

    // Context
    parts.push('captured in a character portrait style, well-lit with attention to facial details and expression');

    return parts.join(', ') + '.';
  }

  /**
   * Build enemy scene (narrative)
   */
  private buildEnemyScene(data: any): string {
    const parts: string[] = [];

    if (data.name && data.type) {
      parts.push(`${data.name}, a fearsome ${data.type}`);
    }

    if (data.description) {
      parts.push(data.description);
    }

    // Power indicators
    if (data.level > 50 || data.isBoss) {
      parts.push('radiating immense power and menace');
    }

    // Action
    parts.push('posed in an aggressive stance, ready for combat');

    // Context
    parts.push('The creature is the central focus, dramatically lit to emphasize its threatening presence');

    return parts.join(', ') + '.';
  }

  /**
   * Build environment scene (narrative)
   */
  private buildEnvironmentScene(data: any): string {
    const parts: string[] = [];

    if (data.name) {
      parts.push(`The ${data.biome || 'landscape'} of ${data.name}`);
    }

    if (data.description) {
      parts.push(data.description);
    }

    // Atmosphere
    if (data.climate) {
      parts.push(`under ${data.climate} conditions`);
    }

    // Mood
    if (data.lore) {
      parts.push('with an atmospheric, mysterious quality');
    }

    // Context
    parts.push('The scene is captured in a wide-angle view, showcasing the expansive environment with rich detail in both foreground and background elements');

    return parts.join(', ') + '.';
  }

  /**
   * Build spell scene (narrative)
   */
  private buildSpellScene(data: any): string {
    const parts: string[] = [];

    if (data.name) {
      parts.push(`The magical spell ${data.name}`);
    }

    if (data.school) {
      parts.push(`manifesting as ${data.school} magic`);
    }

    // Visual effects based on school
    const schoolEffects: Record<string, string> = {
      fire: 'with roaring flames and orange-red energy swirling in dynamic patterns',
      ice: 'with crystalline frost formations and cool blue luminescence',
      nature: 'with verdant vines, leaves, and green life energy spiraling outward',
      arcane: 'with purple mystical runes and ethereal energy patterns',
      holy: 'with golden radiant light and divine energy beams',
      shadow: 'with dark tendrils and violet-black energy wisps',
    };

    if (data.school && schoolEffects[data.school]) {
      parts.push(schoolEffects[data.school]);
    }

    if (data.description) {
      parts.push(data.description);
    }

    // Context
    parts.push('The magical effect is captured mid-cast, showing the spell energy at its most visually dramatic moment');

    return parts.join(', ') + '.';
  }

  /**
   * Get subject line
   */
  private getSubject(options: PromptBuilderOptions): string {
    const { entityData } = options;
    return entityData.name || entityData.description || 'game asset';
  }

  /**
   * Get composition details
   */
  private getComposition(options: PromptBuilderOptions): string {
    const { entityType, cameraAngle } = options;
    const type = entityType.toLowerCase();

    const parts: string[] = [];

    if (type.includes('item')) {
      parts.push('centered, floating, clean background');
    } else if (type.includes('character') || type.includes('npc')) {
      parts.push('portrait composition, rule of thirds');
    } else if (type.includes('environment')) {
      parts.push('wide shot, depth of field, foreground and background elements');
    } else {
      parts.push('balanced composition, clear focal point');
    }

    if (cameraAngle) {
      parts.push(cameraAngle);
    }

    return parts.join(', ');
  }

  /**
   * Get action description
   */
  private getAction(options: PromptBuilderOptions): string | null {
    const { entityType, entityData } = options;
    const type = entityType.toLowerCase();

    if (type.includes('enemy') || type.includes('boss')) {
      return 'in aggressive combat stance';
    } else if (type.includes('spell')) {
      return 'spell energy actively manifesting';
    }

    return null;
  }

  /**
   * Get setting description
   */
  private getSetting(options: PromptBuilderOptions): string {
    const { entityType, entityData } = options;
    const type = entityType.toLowerCase();

    if (type.includes('item')) {
      return 'isolated on clean neutral background';
    } else if (type.includes('environment') || type.includes('zone')) {
      return entityData.biome || entityData.environment || 'fantasy landscape';
    } else if (type.includes('character')) {
      return 'neutral portrait background with subtle depth';
    }

    return 'fantasy game setting';
  }

  /**
   * Build camera details (photographer language)
   */
  private buildCameraDetails(options: PromptBuilderOptions): string {
    const parts: string[] = [];

    if (options.photorealisticMode) {
      parts.push('photographed with professional camera');
    }

    if (options.lensType) {
      parts.push(`using ${options.lensType}`);
    }

    if (options.cameraAngle) {
      parts.push(`shot from ${options.cameraAngle}`);
    }

    if (options.photorealisticMode) {
      parts.push('sharp focus, proper exposure, natural depth of field');
    }

    return parts.join(', ');
  }

  /**
   * Get style as narrative
   */
  private getStyleNarrative(style: string): string {
    const narratives: Record<string, string> = {
      'pixel-art': 'The image is rendered in a retro pixel art style reminiscent of classic 16-bit games, with distinct pixels visible and a limited color palette.',
      'fantasy-realistic': 'The image is rendered in a realistic fantasy art style, with detailed textures, proper lighting, and lifelike materials while maintaining magical elements.',
      'anime': 'The image follows an anime art style with vibrant colors, expressive features, and the characteristic aesthetic of Japanese animation.',
      'painterly': 'The image has a painterly quality with visible brushstrokes, artistic interpretation, and the feel of a traditional painting.',
      'sketch': 'The image appears as a hand-drawn pencil sketch with crosshatching, shading, and the characteristic marks of pencil on paper.',
      'comic-book': 'The image follows a comic book art style with bold outlines, dynamic composition, and the visual language of graphic novels.',
      'low-poly-3d': 'The image is rendered in a low-poly 3D style with geometric shapes, flat shading, and a stylized polygonal aesthetic.',
      'isometric': 'The image uses an isometric perspective, perfect for game assets, showing the subject from an elevated angle with parallel projection.',
      'oil-painting': 'The image resembles a classical oil painting with rich colors, layered brushwork, and the texture and depth of traditional oil painting techniques.',
      'watercolor': 'The image has the soft, translucent quality of watercolor painting with flowing colors, wet edges, and the characteristic bloom of watercolor on paper.',
    };

    return narratives[style] || `The image is rendered in a ${style} artistic style.`;
  }

  /**
   * Build the final prompt based on model type
   */
  build(options: PromptBuilderOptions): string {
    // Gemini prefers narrative descriptions
    if (options.model.includes('gemini')) {
      return this.buildNarrative(options);
    }

    // DALL-E 3 works well with structured prompts
    if (options.model === 'dall-e-3') {
      return this.buildStructured(options);
    }

    // DALL-E 2 fallback
    return this.buildNarrative(options);
  }
}

// Global prompt builder instance
export const globalPromptBuilder = new PromptBuilder();
