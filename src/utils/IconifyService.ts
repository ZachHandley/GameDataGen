/**
 * Iconify integration for downloading free SVG icons
 * API: https://api.iconify.design/{prefix}/{name}.svg
 */

export interface IconifyIcon {
  prefix: string; // Icon set (e.g., 'game-icons', 'mdi', 'fa')
  name: string; // Icon name (e.g., 'sword', 'shield')
  color?: string; // Hex color (without #)
  width?: number; // Width in pixels
  height?: number; // Height in pixels
  rotate?: 90 | 180 | 270; // Rotation
  flip?: 'horizontal' | 'vertical' | 'horizontal,vertical';
}

export interface IconifyDownloadOptions {
  outputDir?: string; // Where to save SVGs
  addBox?: boolean; // Add viewBox rectangle
  forceDownload?: boolean; // Browser download header
}

export interface IconifySearchResult {
  prefix: string;
  name: string;
  tags: string[];
  category?: string;
}

/**
 * Iconify service for downloading and managing icons
 */
export class IconifyService {
  private baseUrl = 'https://api.iconify.design';
  private backupUrls = [
    'https://api.simplesvg.com',
    'https://api.unisvg.com',
  ];
  private cache: Map<string, string> = new Map(); // Cache SVG content

  /**
   * Build Iconify API URL
   */
  private buildUrl(icon: IconifyIcon, options?: IconifyDownloadOptions): string {
    const { prefix, name, color, width, height, rotate, flip } = icon;
    const params = new URLSearchParams();

    if (color) {
      // Replace # with %23 for URL encoding
      const cleanColor = color.replace('#', '');
      params.set('color', cleanColor);
    }

    if (width) params.set('width', width.toString());
    if (height) params.set('height', height.toString());
    if (rotate) params.set('rotate', rotate.toString());
    if (flip) params.set('flip', flip);

    if (options?.addBox) params.set('box', '1');
    if (options?.forceDownload) params.set('download', '1');

    const queryString = params.toString();
    const url = `${this.baseUrl}/${prefix}/${name}.svg`;

    return queryString ? `${url}?${queryString}` : url;
  }

  /**
   * Download an icon as SVG string
   */
  async downloadIcon(icon: IconifyIcon): Promise<string> {
    const cacheKey = `${icon.prefix}:${icon.name}`;

    // Check cache
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    const url = this.buildUrl(icon);

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to download icon: ${response.status} ${response.statusText}`);
      }

      const svg = await response.text();

      // Cache the result
      this.cache.set(cacheKey, svg);

      return svg;
    } catch (error) {
      // Try backup URLs
      for (const backupUrl of this.backupUrls) {
        try {
          const backupFullUrl = url.replace(this.baseUrl, backupUrl);
          const response = await fetch(backupFullUrl);

          if (response.ok) {
            const svg = await response.text();
            this.cache.set(cacheKey, svg);
            return svg;
          }
        } catch {
          continue;
        }
      }

      throw new Error(
        `Failed to download icon from all sources: ${icon.prefix}/${icon.name}`
      );
    }
  }

  /**
   * Download multiple icons in parallel
   */
  async downloadIcons(icons: IconifyIcon[]): Promise<Map<string, string>> {
    const results = new Map<string, string>();

    const promises = icons.map(async (icon) => {
      try {
        const svg = await this.downloadIcon(icon);
        const key = `${icon.prefix}:${icon.name}`;
        results.set(key, svg);
      } catch (error) {
        console.error(`Failed to download ${icon.prefix}/${icon.name}:`, error);
      }
    });

    await Promise.all(promises);

    return results;
  }

  /**
   * Save icon to file system
   */
  async saveIcon(
    icon: IconifyIcon,
    outputDir: string = './output/icons'
  ): Promise<string> {
    const svg = await this.downloadIcon(icon);
    const fs = await import('fs/promises');

    // Create output directory
    await fs.mkdir(outputDir, { recursive: true });

    // Generate filename
    const filename = `${icon.prefix}_${icon.name}.svg`;
    const filepath = `${outputDir}/${filename}`;

    // Write SVG file
    await fs.writeFile(filepath, svg);

    return filepath;
  }

  /**
   * Save multiple icons
   */
  async saveIcons(
    icons: IconifyIcon[],
    outputDir: string = './output/icons'
  ): Promise<string[]> {
    const filepaths: string[] = [];

    for (const icon of icons) {
      try {
        const filepath = await this.saveIcon(icon, outputDir);
        filepaths.push(filepath);
      } catch (error) {
        console.error(`Failed to save ${icon.prefix}/${icon.name}:`, error);
      }
    }

    return filepaths;
  }

  /**
   * Get direct URL for an icon (for embedding in HTML/CSS)
   */
  getIconUrl(icon: IconifyIcon, options?: IconifyDownloadOptions): string {
    return this.buildUrl(icon, options);
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
  getCacheStats(): { size: number; icons: string[] } {
    return {
      size: this.cache.size,
      icons: Array.from(this.cache.keys()),
    };
  }
}

/**
 * Icon pack definitions for common game content
 */
export const GAME_ICON_PACKS = {
  // Weapons
  weapons: {
    sword: { prefix: 'game-icons', name: 'sword' },
    axe: { prefix: 'game-icons', name: 'axe' },
    bow: { prefix: 'game-icons', name: 'bow-arrow' },
    staff: { prefix: 'game-icons', name: 'wizard-staff' },
    dagger: { prefix: 'game-icons', name: 'dagger' },
    hammer: { prefix: 'game-icons', name: 'war-hammer' },
    spear: { prefix: 'game-icons', name: 'spear' },
    mace: { prefix: 'game-icons', name: 'mace' },
  },

  // Armor
  armor: {
    helmet: { prefix: 'game-icons', name: 'helmet' },
    chestplate: { prefix: 'game-icons', name: 'chest-armor' },
    shield: { prefix: 'game-icons', name: 'shield' },
    boots: { prefix: 'game-icons', name: 'boots' },
    gloves: { prefix: 'game-icons', name: 'gloves' },
  },

  // Consumables
  consumables: {
    healthPotion: { prefix: 'game-icons', name: 'health-potion' },
    manaPotion: { prefix: 'game-icons', name: 'potion-ball' },
    food: { prefix: 'game-icons', name: 'meal' },
    drink: { prefix: 'game-icons', name: 'beer-stein' },
    scroll: { prefix: 'game-icons', name: 'scroll-unfurled' },
  },

  // Resources
  resources: {
    gold: { prefix: 'game-icons', name: 'gold-bar' },
    wood: { prefix: 'game-icons', name: 'wood-pile' },
    ore: { prefix: 'game-icons', name: 'ore' },
    herb: { prefix: 'game-icons', name: 'herb' },
    gem: { prefix: 'game-icons', name: 'gem' },
    leather: { prefix: 'game-icons', name: 'leather' },
  },

  // Magic
  magic: {
    fireball: { prefix: 'game-icons', name: 'fireball' },
    lightning: { prefix: 'game-icons', name: 'lightning-bolt' },
    heal: { prefix: 'game-icons', name: 'healing' },
    shield: { prefix: 'game-icons', name: 'magic-shield' },
    teleport: { prefix: 'game-icons', name: 'teleport' },
    summon: { prefix: 'game-icons', name: 'summoning' },
  },

  // Enemies
  enemies: {
    dragon: { prefix: 'game-icons', name: 'dragon' },
    skeleton: { prefix: 'game-icons', name: 'skeleton' },
    orc: { prefix: 'game-icons', name: 'orc-head' },
    goblin: { prefix: 'game-icons', name: 'imp' },
    demon: { prefix: 'game-icons', name: 'daemon-skull' },
    zombie: { prefix: 'game-icons', name: 'zombie' },
  },

  // NPCs
  npcs: {
    merchant: { prefix: 'game-icons', name: 'merchant' },
    guard: { prefix: 'game-icons', name: 'swordman' },
    mage: { prefix: 'game-icons', name: 'wizard-face' },
    priest: { prefix: 'game-icons', name: 'prayer' },
    blacksmith: { prefix: 'game-icons', name: 'anvil' },
    farmer: { prefix: 'game-icons', name: 'farmer' },
  },

  // UI
  ui: {
    quest: { prefix: 'game-icons', name: 'scroll-quill' },
    achievement: { prefix: 'game-icons', name: 'achievement' },
    settings: { prefix: 'mdi', name: 'cog' },
    map: { prefix: 'game-icons', name: 'treasure-map' },
    inventory: { prefix: 'game-icons', name: 'backpack' },
    skills: { prefix: 'game-icons', name: 'skills' },
  },
};

/**
 * Helper function to get icon by category and name
 */
export function getGameIcon(category: keyof typeof GAME_ICON_PACKS, name: string): IconifyIcon | undefined {
  return (GAME_ICON_PACKS[category] as any)[name];
}

/**
 * Helper function to suggest icons based on entity type
 */
export function suggestIconForEntity(entityType: string, entityData: any): IconifyIcon {
  const type = entityType.toLowerCase();

  // Default mapping
  if (type.includes('weapon')) {
    return { prefix: 'game-icons', name: 'crossed-swords' };
  }
  if (type.includes('armor')) {
    return { prefix: 'game-icons', name: 'chest-armor' };
  }
  if (type.includes('potion') || type.includes('consumable')) {
    return { prefix: 'game-icons', name: 'potion-ball' };
  }
  if (type.includes('spell') || type.includes('magic')) {
    return { prefix: 'game-icons', name: 'magic-swirl' };
  }
  if (type.includes('quest')) {
    return { prefix: 'game-icons', name: 'scroll-quill' };
  }
  if (type.includes('npc')) {
    return { prefix: 'game-icons', name: 'person' };
  }
  if (type.includes('enemy') || type.includes('boss')) {
    return { prefix: 'game-icons', name: 'skull' };
  }

  // Default
  return { prefix: 'game-icons', name: 'perspective-dice-six' };
}

// Global iconify service instance
export const globalIconify = new IconifyService();
