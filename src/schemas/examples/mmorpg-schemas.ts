import { z } from 'zod';

/**
 * Example schemas for an MMORPG
 * Users can define their own schemas based on their game needs
 */

// ============================================================
// Foundation Schemas (no dependencies)
// ============================================================

export const RaceSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  traits: z.array(z.string()),
  startingStats: z.object({
    strength: z.number(),
    agility: z.number(),
    intelligence: z.number(),
    vitality: z.number(),
  }),
  lore: z.string(),
});

export const ClassSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  role: z.enum(['tank', 'healer', 'dps', 'support']),
  abilities: z.array(
    z.object({
      name: z.string(),
      description: z.string(),
      level: z.number(),
    })
  ),
  primaryStat: z.enum(['strength', 'agility', 'intelligence', 'vitality']),
});

export const ProfessionSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum(['gathering', 'crafting', 'service']),
  skills: z.array(
    z.object({
      name: z.string(),
      description: z.string(),
      level: z.number(),
    })
  ),
});

export const FactionSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  alignment: z.enum(['good', 'neutral', 'evil']),
  territory: z.string(),
  rivals: z.array(z.string()).optional(),
  allies: z.array(z.string()).optional(),
  lore: z.string(),
});

// ============================================================
// World Building Schemas
// ============================================================

export const ZoneSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  level: z.object({
    min: z.number(),
    max: z.number(),
  }),
  environment: z.enum(['forest', 'desert', 'mountains', 'swamp', 'plains', 'tundra', 'underground', 'coastal']),
  climate: z.string(),
  factions: z.array(z.string()), // Faction IDs
  lore: z.string(),
  pointsOfInterest: z.array(
    z.object({
      name: z.string(),
      description: z.string(),
      coordinates: z.object({ x: z.number(), y: z.number() }),
    })
  ),
});

// ============================================================
// Character/NPC Schemas (depend on Zone, Faction)
// ============================================================

export const NPCSchema = z.object({
  id: z.string(),
  name: z.string(),
  title: z.string().optional(),
  race: z.string(), // Race ID
  class: z.string().optional(), // Class ID
  level: z.number(),
  faction: z.string(), // Faction ID
  location: z.object({
    zone: z.string(), // Zone ID
    coordinates: z.object({ x: z.number(), y: z.number() }).optional(),
  }),
  personality: z.string(),
  dialogue: z.array(
    z.object({
      trigger: z.string(),
      text: z.string(),
    })
  ),
  vendor: z
    .object({
      type: z.enum(['general', 'weapons', 'armor', 'consumables', 'profession']),
      stock: z.array(z.string()), // Item IDs
    })
    .optional(),
  questGiver: z.boolean().optional(),
});

export const EnemySchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['beast', 'humanoid', 'undead', 'demon', 'elemental', 'dragon']),
  level: z.number(),
  faction: z.string().optional(), // Faction ID
  location: z.object({
    zone: z.string(), // Zone ID
    spawnPoints: z.array(z.object({ x: z.number(), y: z.number() })),
  }),
  stats: z.object({
    health: z.number(),
    damage: z.number(),
    armor: z.number(),
  }),
  abilities: z.array(
    z.object({
      name: z.string(),
      description: z.string(),
      cooldown: z.number(),
    })
  ),
  loot: z.array(
    z.object({
      itemId: z.string(), // Item ID
      dropChance: z.number(), // 0-1
    })
  ),
  lore: z.string(),
});

// ============================================================
// Items (can reference Professions, Enemies)
// ============================================================

export const ItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum(['weapon', 'armor', 'consumable', 'quest', 'material', 'misc']),
  rarity: z.enum(['trash', 'common', 'uncommon', 'rare', 'epic', 'legendary']),
  level: z.number().optional(),
  stats: z
    .object({
      strength: z.number().optional(),
      agility: z.number().optional(),
      intelligence: z.number().optional(),
      vitality: z.number().optional(),
      armor: z.number().optional(),
      damage: z.number().optional(),
    })
    .optional(),
  profession: z.string().optional(), // Profession ID (if crafted)
  craftingMaterials: z
    .array(
      z.object({
        itemId: z.string(),
        quantity: z.number(),
      })
    )
    .optional(),
  value: z.number(), // Gold value
  stackable: z.boolean(),
  lore: z.string().optional(),
});

// ============================================================
// Quests (depend on NPCs, Items, Enemies, Zones)
// ============================================================

export const QuestSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  questGiver: z.string(), // NPC ID
  level: z.number(),
  type: z.enum(['main', 'side', 'daily', 'repeatable', 'chain']),
  objectives: z.array(
    z.object({
      type: z.enum(['kill', 'collect', 'talk', 'explore', 'escort']),
      description: z.string(),
      target: z.string().optional(), // Enemy/NPC/Item/Zone ID
      quantity: z.number().optional(),
    })
  ),
  rewards: z.object({
    experience: z.number(),
    gold: z.number(),
    items: z.array(z.string()).optional(), // Item IDs
    reputation: z
      .object({
        faction: z.string(), // Faction ID
        amount: z.number(),
      })
      .optional(),
  }),
  prerequisites: z.array(z.string()).optional(), // Quest IDs
  nextQuest: z.string().optional(), // Quest ID (for chains)
  lore: z.string(),
});

// ============================================================
// Type exports
// ============================================================

export type Race = z.infer<typeof RaceSchema>;
export type Class = z.infer<typeof ClassSchema>;
export type Profession = z.infer<typeof ProfessionSchema>;
export type Faction = z.infer<typeof FactionSchema>;
export type Zone = z.infer<typeof ZoneSchema>;
export type NPC = z.infer<typeof NPCSchema>;
export type Enemy = z.infer<typeof EnemySchema>;
export type Item = z.infer<typeof ItemSchema>;
export type Quest = z.infer<typeof QuestSchema>;
