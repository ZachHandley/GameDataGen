import { z } from 'zod';

/**
 * Event system schemas - seasonal events, world events, random encounters
 */

// ============================================================
// Event Schemas
// ============================================================

export const EventSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum([
    'seasonal',     // Holiday events (Christmas, Halloween)
    'world',        // Server-wide events
    'zone',         // Zone-specific events
    'random',       // Random encounters while playing
    'timed',        // Timed events (every Saturday at 8PM)
    'triggered',    // Quest/achievement triggered
  ]),
  description: z.string(),

  // Activation conditions
  activationConditions: z.object({
    // Time-based
    startDate: z.string().optional(),  // ISO date
    endDate: z.string().optional(),
    recurringSchedule: z.string().optional(),  // Cron-like: "0 20 * * 6" = Saturdays 8PM

    // Level requirements
    minLevel: z.number().optional(),
    maxLevel: z.number().optional(),

    // Prerequisites
    requiredQuests: z.array(z.string()).optional(),
    requiredAchievements: z.array(z.string()).optional(),

    // Random chance
    randomChance: z.number().optional(),  // 0-1, e.g., 0.05 = 5% chance on zone enter

    // Location triggers
    triggerZones: z.array(z.string()).optional(),  // Zone IDs
    triggerLocations: z.array(
      z.object({
        zone: z.string(),
        position: z.object({ x: z.number(), y: z.number() }),
        radius: z.number(),
      })
    ).optional(),

    // Player count
    minPlayers: z.number().optional(),  // Requires X players in zone

    // Custom trigger
    customTrigger: z.string().optional(),  // "kill_100_enemies", "gather_10_herbs"
  }),

  // Event content
  content: z.object({
    // NPCs that spawn during event
    eventNPCs: z.array(
      z.object({
        npcId: z.string(),
        spawnLocations: z.array(
          z.object({
            zone: z.string(),
            position: z.object({ x: z.number(), y: z.number() }),
          })
        ),
        temporary: z.boolean(),  // Removed when event ends
      })
    ).optional(),

    // Event bosses
    eventBosses: z.array(
      z.object({
        bossId: z.string(),
        spawnZone: z.string(),
        spawnPosition: z.object({ x: z.number(), y: z.number() }),
        spawnInterval: z.number().optional(),  // Respawn time in seconds
        announceSpawn: z.boolean().optional(),  // Server-wide announcement
      })
    ).optional(),

    // Quests available during event
    eventQuests: z.array(z.string()).optional(),  // Quest IDs

    // Zone modifications
    zoneModifications: z.array(
      z.object({
        zone: z.string(),
        decoration: z.string().optional(),  // "christmas_lights", "halloween_fog"
        weatherOverride: z.string().optional(),  // "snow", "fog"
        musicOverride: z.string().optional(),
      })
    ).optional(),

    // Items available during event
    limitedItems: z.array(z.string()).optional(),  // Item IDs

    // Rewards
    participationRewards: z.object({
      experience: z.number().optional(),
      gold: z.number().optional(),
      items: z.array(z.string()).optional(),
      title: z.string().optional(),
      achievement: z.string().optional(),
    }).optional(),
  }),

  lore: z.string(),
});

// ============================================================
// Event Boss (extends normal boss with event-specific data)
// ============================================================

export const EventBossSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum(['seasonal', 'world_event', 'random_encounter']),
  level: z.number(),

  // Event association
  eventId: z.string().optional(),  // Which event spawns this boss

  // Spawn behavior
  spawnBehavior: z.object({
    type: z.enum(['scheduled', 'random', 'triggered']),
    schedule: z.string().optional(),  // "0 20 * * 6" for scheduled
    randomChance: z.number().optional(),  // For random spawns
    triggerCondition: z.string().optional(),  // "kill_boss_x"
    announceSpawn: z.boolean(),
    announceMessage: z.string().optional(),
  }),

  // Location
  possibleZones: z.array(z.string()),
  preferredSpawnPoints: z.array(
    z.object({
      zone: z.string(),
      position: z.object({ x: z.number(), y: z.number() }),
      weight: z.number(),  // Weighted random selection
    })
  ),

  // Combat
  health: z.number(),
  damage: z.number(),
  armor: z.number(),
  abilities: z.array(
    z.object({
      name: z.string(),
      description: z.string(),
      cooldown: z.number(),
      areaOfEffect: z.number().optional(),
    })
  ),

  // Loot (special event loot)
  guaranteedLoot: z.array(z.string()).optional(),  // Item IDs
  lootTable: z.array(
    z.object({
      itemId: z.string(),
      dropChance: z.number(),
      maxDrops: z.number().optional(),  // Per kill
    })
  ),

  // Scaling
  scalesWithPlayers: z.boolean().optional(),  // Health/damage scales with nearby player count

  lore: z.string(),
});

// ============================================================
// Random Encounter (things that happen while playing)
// ============================================================

export const RandomEncounterSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum([
    'enemy_ambush',
    'treasure_find',
    'npc_encounter',
    'environmental_hazard',
    'mystery_event',
  ]),

  // Trigger conditions
  triggerConditions: z.object({
    zones: z.array(z.string()).optional(),  // Which zones can it happen in
    biome: z.string().optional(),  // "forest", "desert"
    playerLevel: z.object({
      min: z.number(),
      max: z.number(),
    }).optional(),
    timeOfDay: z.enum(['day', 'night', 'dusk', 'dawn', 'any']).optional(),
    weather: z.array(z.string()).optional(),  // ["rain", "storm"]
    baseChance: z.number(),  // Base chance per minute of gameplay
    cooldown: z.number().optional(),  // Minimum time between occurrences (seconds)
  }),

  // Outcomes (one is chosen)
  outcomes: z.array(
    z.object({
      weight: z.number(),  // Weighted random selection
      type: z.enum(['combat', 'loot', 'dialogue', 'choice', 'consequence']),
      description: z.string(),

      // Combat outcome
      enemies: z.array(
        z.object({
          enemyId: z.string(),
          count: z.number(),
          level: z.number().optional(),  // Override enemy level
        })
      ).optional(),

      // Loot outcome
      loot: z.array(
        z.object({
          itemId: z.string(),
          quantity: z.number(),
          chance: z.number(),
        })
      ).optional(),

      // Dialogue outcome
      npcId: z.string().optional(),
      dialogue: z.string().optional(),

      // Choice outcome
      choices: z.array(
        z.object({
          text: z.string(),
          consequence: z.string(),  // What happens if chosen
          rewardId: z.string().optional(),
        })
      ).optional(),

      // Consequence (debuff, damage, etc.)
      consequence: z.object({
        type: z.enum(['damage', 'debuff', 'item_loss', 'teleport']),
        value: z.any(),
      }).optional(),
    })
  ),

  // Rewards
  baseRewards: z.object({
    experience: z.number().optional(),
    gold: z.number().optional(),
  }).optional(),
});

// ============================================================
// Type exports
// ============================================================

export type Event = z.infer<typeof EventSchema>;
export type EventBoss = z.infer<typeof EventBossSchema>;
export type RandomEncounter = z.infer<typeof RandomEncounterSchema>;
