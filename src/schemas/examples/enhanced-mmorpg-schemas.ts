import { z } from 'zod';

/**
 * Enhanced MMORPG schemas with spatial awareness, leveling, and complex relationships
 */

// ============================================================
// Core Vector/Position Types
// ============================================================

export const Vector3Schema = z.object({
  x: z.number(),
  y: z.number(),
  z: z.number().optional(),
});

export const BoundingBoxSchema = z.object({
  min: Vector3Schema,
  max: Vector3Schema,
});

// ============================================================
// Enhanced Zone with Spatial Data
// ============================================================

export const EnhancedZoneSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  levelRange: z.object({
    min: z.number(),
    max: z.number(),
  }),
  // Spatial data
  bounds: BoundingBoxSchema,
  mapSize: z.object({
    width: z.number(),
    height: z.number(),
  }),
  biome: z.enum([
    'forest',
    'desert',
    'mountains',
    'swamp',
    'plains',
    'tundra',
    'underground',
    'coastal',
  ]),
  elevation: z.object({
    min: z.number(),
    max: z.number(),
  }),
  // Natural features
  hasRivers: z.boolean().optional(),
  hasMountains: z.boolean().optional(),
  vegetationDensity: z.number().min(0).max(1), // 0-1
  // Factions present
  factions: z.array(z.string()),
  // Points of interest
  pointsOfInterest: z.array(
    z.object({
      name: z.string(),
      type: z.enum(['landmark', 'town', 'dungeon', 'camp', 'shrine']),
      position: Vector3Schema,
    })
  ),
  lore: z.string(),
});

// ============================================================
// Enhanced NPC with Tasklist and Spatial Awareness
// ============================================================

export const TaskSchema = z.object({
  time: z.string(), // "08:00" or cron-like
  action: z.enum(['idle', 'walk', 'work', 'sleep', 'patrol', 'trade']),
  location: Vector3Schema.optional(),
  duration: z.number().optional(), // in seconds
  description: z.string().optional(),
});

export const EnhancedNPCSchema = z.object({
  id: z.string(),
  name: z.string(),
  title: z.string().optional(),
  race: z.string(),
  class: z.string().optional(),
  level: z.number(),
  faction: z.string(),
  // Spatial data
  homeZone: z.string(), // Zone ID
  spawnPosition: Vector3Schema,
  wanderRadius: z.number().optional(), // How far they wander
  bounds: BoundingBoxSchema,
  // Appearance
  appearance: z.object({
    height: z.number(), // in meters
    build: z.enum(['slim', 'average', 'muscular', 'heavy']),
    hairColor: z.string(),
    eyeColor: z.string(),
    skinTone: z.string(),
    distinguishingFeatures: z.string().optional(),
    clothing: z.string(),
  }),
  // Behavior
  personality: z.string(),
  tasklist: z.array(TaskSchema).optional(), // Daily routine
  dialogueTree: z.array(
    z.object({
      trigger: z.string(),
      condition: z.string().optional(), // Quest state, faction, etc.
      text: z.string(),
      responses: z
        .array(
          z.object({
            text: z.string(),
            nextNode: z.string().optional(),
          })
        )
        .optional(),
    })
  ),
  // Vendor info
  vendor: z
    .object({
      type: z.enum(['general', 'weapons', 'armor', 'consumables', 'profession']),
      stockIds: z.array(z.string()), // Item IDs
      restockInterval: z.number().optional(), // in seconds
    })
    .optional(),
  questGiver: z.boolean().optional(),
});

// ============================================================
// Dungeon (Composite Entity)
// ============================================================

export const DungeonRoomSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['entrance', 'corridor', 'chamber', 'boss_room', 'treasure']),
  position: Vector3Schema,
  bounds: BoundingBoxSchema,
  enemies: z.array(
    z.object({
      enemyId: z.string(),
      count: z.number(),
      spawnPosition: Vector3Schema,
    })
  ),
  loot: z.array(
    z.object({
      itemId: z.string(),
      position: Vector3Schema.optional(),
      guaranteed: z.boolean().optional(),
    })
  ),
  connectedTo: z.array(z.string()), // Room IDs
  description: z.string(),
});

export const DungeonSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum(['dungeon', 'raid', 'scenario']),
  difficulty: z.enum(['normal', 'heroic', 'mythic']),
  levelRequirement: z.object({
    min: z.number(),
    recommended: z.number(),
  }),
  playerCount: z.object({
    min: z.number(),
    max: z.number(),
  }),
  // Location
  entranceZone: z.string(), // Zone ID
  entrancePosition: Vector3Schema,
  // Structure
  rooms: z.array(DungeonRoomSchema),
  bosses: z.array(
    z.object({
      enemyId: z.string(),
      roomId: z.string(),
      order: z.number(), // 1st boss, 2nd boss, etc.
    })
  ),
  // Rewards
  completionRewards: z.object({
    experience: z.number(),
    gold: z.number(),
    items: z.array(z.string()), // Item IDs
  }),
  // Requirements
  requiredQuests: z.array(z.string()).optional(),
  requiredItem: z.string().optional(), // Key, attunement, etc.
  lore: z.string(),
  estimatedDuration: z.number(), // in minutes
});

// ============================================================
// Questline (Chain of quests)
// ============================================================

export const QuestlineSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum(['main', 'faction', 'profession', 'legendary']),
  levelRange: z.object({
    start: z.number(),
    end: z.number(),
  }),
  quests: z.array(
    z.object({
      questId: z.string(),
      order: z.number(),
      optional: z.boolean().optional(), // Can be skipped
      branchId: z.string().optional(), // For branching storylines
    })
  ),
  culmination: z
    .object({
      type: z.enum(['dungeon', 'raid', 'boss_fight', 'finale_quest']),
      targetId: z.string(), // Dungeon ID, Quest ID, etc.
    })
    .optional(),
  rewards: z.object({
    title: z.string().optional(),
    achievement: z.string().optional(),
    uniqueItem: z.string().optional(), // Legendary item, etc.
  }),
  lore: z.string(),
});

// ============================================================
// World Boss
// ============================================================

export const WorldBossSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  level: z.number(),
  type: z.enum(['dragon', 'demon', 'elemental', 'colossus', 'undead']),
  // Location
  zone: z.string(),
  spawnPosition: Vector3Schema,
  wanderArea: z.object({
    center: Vector3Schema,
    radius: z.number(),
  }).optional(),
  // Stats
  health: z.number(),
  armor: z.number(),
  damage: z.number(),
  // Mechanics
  phases: z.array(
    z.object({
      healthThreshold: z.number(), // % of health
      abilities: z.array(
        z.object({
          name: z.string(),
          description: z.string(),
          cooldown: z.number(),
          areaOfEffect: z.number().optional(),
        })
      ),
    })
  ),
  // Loot
  lootTable: z.array(
    z.object({
      itemId: z.string(),
      dropChance: z.number(),
      quantity: z.number().optional(),
    })
  ),
  // Spawn info
  respawnTime: z.number(), // in seconds
  spawnCondition: z
    .object({
      type: z.enum(['timed', 'event', 'quest'],
      ),
      details: z.string(),
    })
    .optional(),
  lore: z.string(),
});

// ============================================================
// Enhanced Item with Optional Spell Slots
// ============================================================

export const EnhancedItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum([
    'weapon',
    'armor',
    'accessory',
    'consumable',
    'quest',
    'material',
    'misc',
  ]),
  rarity: z.enum(['trash', 'common', 'uncommon', 'rare', 'epic', 'legendary']),
  itemLevel: z.number(),
  levelRequirement: z.number().optional(),
  // Stats
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
  // Spell slots (weapons can cast spells)
  spellSlots: z
    .array(
      z.object({
        slotType: z.enum(['built-in', 'optional', 'enchantment']),
        spellId: z.string().optional(), // Can be empty for optional slots
        charges: z.number().optional(),
        cooldown: z.number().optional(),
      })
    )
    .optional(),
  // Crafting
  craftedBy: z.string().optional(), // Profession ID
  recipe: z
    .object({
      materials: z.array(
        z.object({
          itemId: z.string(),
          quantity: z.number(),
        })
      ),
      skillRequired: z.number(),
    })
    .optional(),
  // Enchanting/socketing
  sockets: z.number().optional(), // Number of gem sockets
  enchantments: z.array(z.string()).optional(), // Enchantment IDs
  // Economy
  value: z.number(), // Gold value
  stackSize: z.number().optional(),
  tradeable: z.boolean().optional(),
  soulbound: z.boolean().optional(),
  lore: z.string().optional(),
});

// ============================================================
// Spell (for spell slots in items)
// ============================================================

export const SpellSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  school: z.enum(['fire', 'ice', 'nature', 'arcane', 'holy', 'shadow', 'physical']),
  type: z.enum(['damage', 'heal', 'buff', 'debuff', 'utility', 'summon']),
  manaCost: z.number(),
  castTime: z.number(), // in seconds
  cooldown: z.number(), // in seconds
  range: z.number(), // in meters
  areaOfEffect: z.number().optional(),
  effects: z.array(
    z.object({
      type: z.string(),
      value: z.number(),
      duration: z.number().optional(),
    })
  ),
  levelRequired: z.number(),
  classRestriction: z.array(z.string()).optional(), // Class IDs
});

// ============================================================
// Type exports
// ============================================================

export type EnhancedZone = z.infer<typeof EnhancedZoneSchema>;
export type EnhancedNPC = z.infer<typeof EnhancedNPCSchema>;
export type Dungeon = z.infer<typeof DungeonSchema>;
export type DungeonRoom = z.infer<typeof DungeonRoomSchema>;
export type Questline = z.infer<typeof QuestlineSchema>;
export type WorldBoss = z.infer<typeof WorldBossSchema>;
export type EnhancedItem = z.infer<typeof EnhancedItemSchema>;
export type Spell = z.infer<typeof SpellSchema>;
export type Task = z.infer<typeof TaskSchema>;
