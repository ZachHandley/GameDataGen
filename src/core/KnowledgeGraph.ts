/**
 * Knowledge Graph system using triplets for rich entity relationships
 * Supports optional relationships, metadata, conditions, and complex queries
 */

export type EntityReference = {
  type: string; // Entity type (e.g., "NPC", "Quest", "Item")
  id: string; // Entity ID
};

export type RelationMetadata = {
  // Optional/weighted relationships
  optional?: boolean;
  weight?: number; // For weighted selection (e.g., loot tables)
  chance?: number; // Drop chance, spawn chance, etc. (0-1)

  // Conditional relationships
  levelRequired?: number;
  questPrerequisites?: string[];
  factionRequired?: string;
  classRequired?: string;

  // Quantitative data
  quantity?: number;
  minQuantity?: number;
  maxQuantity?: number;

  // Spatial data
  coordinates?: { x: number; y: number; z?: number };
  radius?: number;

  // Temporal data
  duration?: number; // in seconds
  cooldown?: number;
  schedule?: Array<{
    time: string; // "08:00" or cron-like
    action: string;
    location?: { x: number; y: number; z?: number };
    duration?: number;
  }>;

  // Loot/rewards
  guaranteed?: boolean;
  scaledToLevel?: boolean;

  // Quest chains
  chainPosition?: number;
  branchType?: 'linear' | 'branching' | 'optional';

  // Custom metadata
  [key: string]: any;
};

/**
 * A triplet relationship: (subject, predicate, object, metadata)
 */
export interface Triplet {
  subject: EntityReference;
  predicate: string; // Relationship type
  object: EntityReference;
  metadata?: RelationMetadata;
}

/**
 * Knowledge graph for managing rich entity relationships
 */
export class KnowledgeGraph {
  private triplets: Triplet[] = [];
  private indexBySubject: Map<string, Triplet[]> = new Map();
  private indexByObject: Map<string, Triplet[]> = new Map();
  private indexByPredicate: Map<string, Triplet[]> = new Map();

  /**
   * Add a triplet to the graph
   */
  addTriplet(triplet: Triplet): void {
    this.triplets.push(triplet);

    // Index by subject
    const subjectKey = `${triplet.subject.type}:${triplet.subject.id}`;
    if (!this.indexBySubject.has(subjectKey)) {
      this.indexBySubject.set(subjectKey, []);
    }
    this.indexBySubject.get(subjectKey)!.push(triplet);

    // Index by object
    const objectKey = `${triplet.object.type}:${triplet.object.id}`;
    if (!this.indexByObject.has(objectKey)) {
      this.indexByObject.set(objectKey, []);
    }
    this.indexByObject.get(objectKey)!.push(triplet);

    // Index by predicate
    if (!this.indexByPredicate.has(triplet.predicate)) {
      this.indexByPredicate.set(triplet.predicate, []);
    }
    this.indexByPredicate.get(triplet.predicate)!.push(triplet);
  }

  /**
   * Add multiple triplets
   */
  addTriplets(triplets: Triplet[]): void {
    for (const triplet of triplets) {
      this.addTriplet(triplet);
    }
  }

  /**
   * Find all triplets where this entity is the subject
   */
  findBySubject(type: string, id: string): Triplet[] {
    const key = `${type}:${id}`;
    return this.indexBySubject.get(key) || [];
  }

  /**
   * Find all triplets where this entity is the object
   */
  findByObject(type: string, id: string): Triplet[] {
    const key = `${type}:${id}`;
    return this.indexByObject.get(key) || [];
  }

  /**
   * Find all triplets with a specific predicate
   */
  findByPredicate(predicate: string): Triplet[] {
    return this.indexByPredicate.get(predicate) || [];
  }

  /**
   * Find triplets matching criteria
   */
  find(criteria: {
    subject?: { type?: string; id?: string };
    predicate?: string;
    object?: { type?: string; id?: string };
    metadata?: Partial<RelationMetadata>;
  }): Triplet[] {
    let results = [...this.triplets];

    if (criteria.subject?.type && criteria.subject?.id) {
      results = this.findBySubject(criteria.subject.type, criteria.subject.id);
    } else if (criteria.subject?.type) {
      results = results.filter((t) => t.subject.type === criteria.subject!.type);
    } else if (criteria.subject?.id) {
      results = results.filter((t) => t.subject.id === criteria.subject!.id);
    }

    if (criteria.predicate) {
      results = results.filter((t) => t.predicate === criteria.predicate);
    }

    if (criteria.object?.type) {
      results = results.filter((t) => t.object.type === criteria.object!.type);
    }

    if (criteria.object?.id) {
      results = results.filter((t) => t.object.id === criteria.object!.id);
    }

    if (criteria.metadata) {
      results = results.filter((t) => {
        if (!t.metadata) return false;
        return Object.entries(criteria.metadata!).every(
          ([key, value]) => t.metadata![key] === value
        );
      });
    }

    return results;
  }

  /**
   * Get all entities related to this one (both directions)
   */
  getRelatedEntities(type: string, id: string): {
    outgoing: Triplet[]; // This entity as subject
    incoming: Triplet[]; // This entity as object
  } {
    return {
      outgoing: this.findBySubject(type, id),
      incoming: this.findByObject(type, id),
    };
  }

  /**
   * Find path between two entities (for quest chains, dependency tracking)
   */
  findPath(
    from: EntityReference,
    to: EntityReference,
    maxDepth: number = 5
  ): Triplet[][] {
    const paths: Triplet[][] = [];
    const visited = new Set<string>();

    const search = (
      current: EntityReference,
      target: EntityReference,
      path: Triplet[],
      depth: number
    ) => {
      if (depth > maxDepth) return;

      const key = `${current.type}:${current.id}`;
      if (visited.has(key)) return;
      visited.add(key);

      const outgoing = this.findBySubject(current.type, current.id);

      for (const triplet of outgoing) {
        const newPath = [...path, triplet];

        if (
          triplet.object.type === target.type &&
          triplet.object.id === target.id
        ) {
          paths.push(newPath);
          continue;
        }

        search(triplet.object, target, newPath, depth + 1);
      }

      visited.delete(key);
    };

    search(from, to, [], 0);
    return paths;
  }

  /**
   * Get all entities of a type that match conditions
   */
  getConditionalRelations(
    subject: EntityReference,
    predicate: string,
    conditions: {
      minLevel?: number;
      maxLevel?: number;
      requiredQuests?: string[];
      requiredFaction?: string;
    }
  ): Triplet[] {
    const triplets = this.find({
      subject: { type: subject.type, id: subject.id },
      predicate,
    });

    return triplets.filter((t) => {
      if (!t.metadata) return true;

      if (conditions.minLevel && t.metadata.levelRequired) {
        if (t.metadata.levelRequired < conditions.minLevel) return false;
      }

      if (conditions.maxLevel && t.metadata.levelRequired) {
        if (t.metadata.levelRequired > conditions.maxLevel) return false;
      }

      if (conditions.requiredQuests && t.metadata.questPrerequisites) {
        const hasAll = t.metadata.questPrerequisites.every((q) =>
          conditions.requiredQuests!.includes(q)
        );
        if (!hasAll) return false;
      }

      if (conditions.requiredFaction && t.metadata.factionRequired) {
        if (t.metadata.factionRequired !== conditions.requiredFaction)
          return false;
      }

      return true;
    });
  }

  /**
   * Sample weighted relationships (for loot tables, spawn selection)
   */
  sampleWeighted(triplets: Triplet[]): Triplet | null {
    const weighted = triplets.filter((t) => t.metadata?.weight);

    if (weighted.length === 0) {
      // No weights, return random
      return triplets[Math.floor(Math.random() * triplets.length)] || null;
    }

    const totalWeight = weighted.reduce(
      (sum, t) => sum + (t.metadata!.weight || 0),
      0
    );
    let random = Math.random() * totalWeight;

    for (const triplet of weighted) {
      random -= triplet.metadata!.weight || 0;
      if (random <= 0) return triplet;
    }

    return weighted[weighted.length - 1] || null;
  }

  /**
   * Get loot drops for an entity (with chance calculations)
   */
  getLootDrops(
    entityType: string,
    entityId: string,
    playerLevel?: number
  ): Array<{
    item: EntityReference;
    quantity: number;
    rolled: boolean;
  }> {
    const drops: Array<{
      item: EntityReference;
      quantity: number;
      rolled: boolean;
    }> = [];

    const lootTriplets = this.find({
      subject: { type: entityType, id: entityId },
      predicate: 'drops',
    });

    for (const triplet of lootTriplets) {
      const meta = triplet.metadata || {};

      // Check level requirements
      if (playerLevel && meta.levelRequired) {
        if (playerLevel < meta.levelRequired) continue;
      }

      // Guaranteed drops
      if (meta.guaranteed) {
        drops.push({
          item: triplet.object,
          quantity: meta.quantity || 1,
          rolled: true,
        });
        continue;
      }

      // Chance-based drops
      const chance = meta.chance || 0.5;
      const rolled = Math.random() < chance;

      if (rolled) {
        const quantity =
          meta.minQuantity && meta.maxQuantity
            ? Math.floor(
                Math.random() * (meta.maxQuantity - meta.minQuantity + 1)
              ) + meta.minQuantity
            : meta.quantity || 1;

        drops.push({
          item: triplet.object,
          quantity,
          rolled: true,
        });
      }
    }

    return drops;
  }

  /**
   * Clear all triplets
   */
  clear(): void {
    this.triplets = [];
    this.indexBySubject.clear();
    this.indexByObject.clear();
    this.indexByPredicate.clear();
  }

  /**
   * Export as JSON
   */
  export(): Triplet[] {
    return [...this.triplets];
  }

  /**
   * Import from JSON
   */
  import(triplets: Triplet[]): void {
    this.clear();
    this.addTriplets(triplets);
  }

  /**
   * Get statistics
   */
  getStats(): {
    totalTriplets: number;
    predicateCount: Record<string, number>;
    entityTypes: Set<string>;
  } {
    const predicateCount: Record<string, number> = {};
    const entityTypes = new Set<string>();

    for (const triplet of this.triplets) {
      predicateCount[triplet.predicate] =
        (predicateCount[triplet.predicate] || 0) + 1;
      entityTypes.add(triplet.subject.type);
      entityTypes.add(triplet.object.type);
    }

    return {
      totalTriplets: this.triplets.length,
      predicateCount,
      entityTypes,
    };
  }
}

// Global knowledge graph instance
export const globalKnowledgeGraph = new KnowledgeGraph();
