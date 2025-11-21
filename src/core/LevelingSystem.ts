/**
 * Leveling system for managing XP budgeting and level scaling
 * Ensures players reach max level through available content
 */

export interface LevelingConfig {
  maxLevel: number;
  baseXP: number; // XP needed for level 2
  xpCurve: 'linear' | 'exponential' | 'logarithmic' | 'custom';
  customCurveMultiplier?: number; // For custom curves
}

export interface ContentXPBudget {
  mainQuests: number; // % of total XP
  sideQuests: number;
  dungeons: number;
  raids: number;
  gathering: number;
  crafting: number;
  exploration: number;
  worldBosses: number;
  dailies: number;
  other: number;
}

export interface LevelRange {
  min: number;
  max: number;
}

export interface QuestXPReward {
  questLevel: number;
  baseXP: number;
  bonusXP?: number;
}

/**
 * Leveling system for XP budgeting and content scaling
 */
export class LevelingSystem {
  private config: LevelingConfig;
  private xpTable: Map<number, number> = new Map(); // Level → Total XP needed
  private budget: ContentXPBudget;

  constructor(
    config: LevelingConfig,
    budget: ContentXPBudget = {
      mainQuests: 0.4,
      sideQuests: 0.15,
      dungeons: 0.2,
      raids: 0.05,
      gathering: 0.05,
      crafting: 0.03,
      exploration: 0.05,
      worldBosses: 0.04,
      dailies: 0.02,
      other: 0.01,
    }
  ) {
    this.config = config;
    this.budget = budget;
    this.generateXPTable();
  }

  /**
   * Generate XP table for all levels
   */
  private generateXPTable(): void {
    this.xpTable.set(1, 0); // Level 1 starts at 0 XP

    for (let level = 2; level <= this.config.maxLevel; level++) {
      const xpForLevel = this.calculateXPForLevel(level);
      const previousTotal = this.xpTable.get(level - 1) || 0;
      this.xpTable.set(level, previousTotal + xpForLevel);
    }
  }

  /**
   * Calculate XP needed to go from level N to level N+1
   */
  private calculateXPForLevel(level: number): number {
    const base = this.config.baseXP;

    switch (this.config.xpCurve) {
      case 'linear':
        return base * level;

      case 'exponential':
        return Math.floor(base * Math.pow(level, 1.5));

      case 'logarithmic':
        return Math.floor(base * (level + Math.log(level + 1) * 10));

      case 'custom':
        const multiplier = this.config.customCurveMultiplier || 1.2;
        return Math.floor(base * Math.pow(level, multiplier));

      default:
        return base * level;
    }
  }

  /**
   * Get total XP needed to reach a specific level
   */
  getTotalXPForLevel(level: number): number {
    return this.xpTable.get(level) || 0;
  }

  /**
   * Get XP needed to go from one level to another
   */
  getXPBetweenLevels(fromLevel: number, toLevel: number): number {
    return this.getTotalXPForLevel(toLevel) - this.getTotalXPForLevel(fromLevel);
  }

  /**
   * Get total XP available in the game
   */
  getTotalXPNeeded(): number {
    return this.getTotalXPForLevel(this.config.maxLevel);
  }

  /**
   * Calculate XP budget for a content type
   */
  getXPBudget(contentType: keyof ContentXPBudget): number {
    const totalXP = this.getTotalXPNeeded();
    const percentage = this.budget[contentType];
    return Math.floor(totalXP * percentage);
  }

  /**
   * Calculate how many pieces of content needed to fill XP budget
   */
  calculateContentCount(
    contentType: keyof ContentXPBudget,
    averageXPPerPiece: number
  ): number {
    const budget = this.getXPBudget(contentType);
    return Math.ceil(budget / averageXPPerPiece);
  }

  /**
   * Generate quest XP reward based on quest level
   */
  calculateQuestXP(
    questLevel: number,
    questType: 'main' | 'side' | 'daily' = 'side',
    difficulty: 'easy' | 'normal' | 'hard' = 'normal'
  ): number {
    const baseXP = this.calculateXPForLevel(questLevel);

    let multiplier = 1.0;

    // Quest type multipliers
    switch (questType) {
      case 'main':
        multiplier = 1.5;
        break;
      case 'side':
        multiplier = 1.0;
        break;
      case 'daily':
        multiplier = 0.8;
        break;
    }

    // Difficulty multipliers
    switch (difficulty) {
      case 'easy':
        multiplier *= 0.8;
        break;
      case 'normal':
        multiplier *= 1.0;
        break;
      case 'hard':
        multiplier *= 1.3;
        break;
    }

    return Math.floor(baseXP * multiplier);
  }

  /**
   * Calculate dungeon XP reward
   */
  calculateDungeonXP(
    dungeonLevel: number,
    type: 'normal' | 'heroic' | 'mythic' = 'normal',
    bossCount: number = 3
  ): number {
    const baseXP = this.calculateXPForLevel(dungeonLevel);

    let multiplier = bossCount * 2; // Base multiplier per boss

    switch (type) {
      case 'normal':
        multiplier *= 1.0;
        break;
      case 'heroic':
        multiplier *= 1.5;
        break;
      case 'mythic':
        multiplier *= 2.0;
        break;
    }

    return Math.floor(baseXP * multiplier);
  }

  /**
   * Suggest level ranges for zones based on max level
   */
  suggestZoneLevelRanges(zoneCount: number): LevelRange[] {
    const maxLevel = this.config.maxLevel;
    const levelsPerZone = Math.floor(maxLevel / zoneCount);
    const ranges: LevelRange[] = [];

    for (let i = 0; i < zoneCount; i++) {
      const min = i * levelsPerZone + 1;
      const max = Math.min((i + 1) * levelsPerZone, maxLevel);
      ranges.push({ min, max });
    }

    // Adjust last zone to include max level
    if (ranges.length > 0) {
      ranges[ranges.length - 1].max = maxLevel;
    }

    return ranges;
  }

  /**
   * Distribute content across level ranges
   */
  distributeContent(
    totalCount: number,
    levelRanges: LevelRange[]
  ): Map<LevelRange, number> {
    const distribution = new Map<LevelRange, number>();

    // Simple even distribution
    const baseCount = Math.floor(totalCount / levelRanges.length);
    const remainder = totalCount % levelRanges.length;

    for (let i = 0; i < levelRanges.length; i++) {
      const count = baseCount + (i < remainder ? 1 : 0);
      distribution.set(levelRanges[i], count);
    }

    return distribution;
  }

  /**
   * Calculate if player can reach max level with available content
   */
  validateXPBudget(availableContent: {
    mainQuestCount: number;
    sideQuestCount: number;
    dungeonCount: number;
    averageQuestLevel: number;
    averageDungeonLevel: number;
  }): {
    valid: boolean;
    totalAvailableXP: number;
    totalRequiredXP: number;
    deficit: number;
    suggestions: string[];
  } {
    const totalRequired = this.getTotalXPNeeded();

    let totalAvailable = 0;

    // Main quests
    totalAvailable +=
      availableContent.mainQuestCount *
      this.calculateQuestXP(availableContent.averageQuestLevel, 'main');

    // Side quests
    totalAvailable +=
      availableContent.sideQuestCount *
      this.calculateQuestXP(availableContent.averageQuestLevel, 'side');

    // Dungeons
    totalAvailable +=
      availableContent.dungeonCount *
      this.calculateDungeonXP(availableContent.averageDungeonLevel);

    const deficit = totalRequired - totalAvailable;
    const suggestions: string[] = [];

    if (deficit > 0) {
      // Suggest additional content
      const additionalMainQuests = Math.ceil(
        deficit /
          this.calculateQuestXP(availableContent.averageQuestLevel, 'main')
      );
      suggestions.push(
        `Add ${additionalMainQuests} more main quests to fill XP gap`
      );

      const additionalDungeons = Math.ceil(
        deficit / this.calculateDungeonXP(availableContent.averageDungeonLevel)
      );
      suggestions.push(
        `Or add ${additionalDungeons} more dungeons to fill XP gap`
      );
    }

    return {
      valid: deficit <= 0,
      totalAvailableXP: totalAvailable,
      totalRequiredXP: totalRequired,
      deficit: Math.max(0, deficit),
      suggestions,
    };
  }

  /**
   * Get XP table as array
   */
  getXPTable(): Array<{ level: number; totalXP: number; xpToNext: number }> {
    const table: Array<{ level: number; totalXP: number; xpToNext: number }> =
      [];

    for (let level = 1; level <= this.config.maxLevel; level++) {
      const totalXP = this.getTotalXPForLevel(level);
      const xpToNext =
        level < this.config.maxLevel
          ? this.calculateXPForLevel(level + 1)
          : 0;

      table.push({ level, totalXP, xpToNext });
    }

    return table;
  }

  /**
   * Update budget allocation
   */
  updateBudget(budget: Partial<ContentXPBudget>): void {
    this.budget = { ...this.budget, ...budget };

    // Validate budget sums to ~1.0
    const total = Object.values(this.budget).reduce((sum, val) => sum + val, 0);
    if (Math.abs(total - 1.0) > 0.01) {
      console.warn(
        `XP budget does not sum to 1.0 (current: ${total.toFixed(2)})`
      );
    }
  }

  /**
   * Get current config
   */
  getConfig(): LevelingConfig {
    return { ...this.config };
  }

  /**
   * Get current budget
   */
  getBudget(): ContentXPBudget {
    return { ...this.budget };
  }
}

// Global leveling system instance (will be initialized by GameDataGen)
export let globalLevelingSystem: LevelingSystem | null = null;

/**
 * Initialize global leveling system
 */
export function initializeLevelingSystem(
  config: LevelingConfig,
  budget?: ContentXPBudget
): LevelingSystem {
  globalLevelingSystem = new LevelingSystem(config, budget);
  return globalLevelingSystem;
}
