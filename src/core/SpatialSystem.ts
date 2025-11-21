/**
 * Spatial system for managing world placement, collision detection,
 * and natural object distribution
 */

export interface Vector3 {
  x: number;
  y: number;
  z?: number;
}

export interface BoundingBox {
  min: Vector3;
  max: Vector3;
}

export interface PlacedObject {
  id: string;
  type: string; // "tree", "house", "npc", "rock", etc.
  position: Vector3;
  rotation?: number; // In radians
  scale?: Vector3;
  bounds: BoundingBox;
  metadata?: Record<string, any>;
}

export interface BiomeConfig {
  name: string;
  elevation: { min: number; max: number }; // 0-1 normalized
  moisture: { min: number; max: number }; // 0-1 normalized
  temperature: { min: number; max: number }; // 0-1 normalized
  objects: {
    type: string;
    density: number; // Objects per square unit
    minSpacing: number; // Minimum distance between objects
    placementRules?: PlacementRule[];
  }[];
}

export interface PlacementRule {
  type: 'near' | 'avoid' | 'on' | 'slope' | 'elevation';
  target?: string; // Object type or feature type
  distance?: { min?: number; max?: number };
  slopeRange?: { min: number; max: number }; // In degrees
  elevationRange?: { min: number; max: number };
  required?: boolean; // If true, rule must be satisfied
}

export interface ZoneMap {
  width: number;
  height: number;
  cellSize: number; // Size of each grid cell
  elevation: number[][]; // Heightmap
  moisture: number[][]; // Moisture map
  temperature: number[][]; // Temperature map
}

/**
 * Spatial grid for fast collision detection and nearest-neighbor queries
 */
export class SpatialGrid {
  private cellSize: number;
  private cells: Map<string, PlacedObject[]> = new Map();
  private objects: Map<string, PlacedObject> = new Map();

  constructor(cellSize: number = 10) {
    this.cellSize = cellSize;
  }

  /**
   * Get cell key for a position
   */
  private getCellKey(x: number, y: number): string {
    const cellX = Math.floor(x / this.cellSize);
    const cellY = Math.floor(y / this.cellSize);
    return `${cellX},${cellY}`;
  }

  /**
   * Add an object to the grid
   */
  addObject(obj: PlacedObject): void {
    this.objects.set(obj.id, obj);

    // Add to all cells the bounding box overlaps
    const minCellX = Math.floor(obj.bounds.min.x / this.cellSize);
    const minCellY = Math.floor(obj.bounds.min.y / this.cellSize);
    const maxCellX = Math.floor(obj.bounds.max.x / this.cellSize);
    const maxCellY = Math.floor(obj.bounds.max.y / this.cellSize);

    for (let cx = minCellX; cx <= maxCellX; cx++) {
      for (let cy = minCellY; cy <= maxCellY; cy++) {
        const key = `${cx},${cy}`;
        if (!this.cells.has(key)) {
          this.cells.set(key, []);
        }
        this.cells.get(key)!.push(obj);
      }
    }
  }

  /**
   * Remove an object from the grid
   */
  removeObject(id: string): boolean {
    const obj = this.objects.get(id);
    if (!obj) return false;

    this.objects.delete(id);

    // Remove from all cells
    for (const [key, objs] of this.cells.entries()) {
      const index = objs.findIndex((o) => o.id === id);
      if (index >= 0) {
        objs.splice(index, 1);
      }
      if (objs.length === 0) {
        this.cells.delete(key);
      }
    }

    return true;
  }

  /**
   * Check if a bounding box collides with any existing objects
   */
  checkCollision(bounds: BoundingBox, excludeId?: string): boolean {
    const minCellX = Math.floor(bounds.min.x / this.cellSize);
    const minCellY = Math.floor(bounds.min.y / this.cellSize);
    const maxCellX = Math.floor(bounds.max.x / this.cellSize);
    const maxCellY = Math.floor(bounds.max.y / this.cellSize);

    for (let cx = minCellX; cx <= maxCellX; cx++) {
      for (let cy = minCellY; cy <= maxCellY; cy++) {
        const key = `${cx},${cy}`;
        const objects = this.cells.get(key) || [];

        for (const obj of objects) {
          if (excludeId && obj.id === excludeId) continue;

          if (this.boundsOverlap(bounds, obj.bounds)) {
            return true;
          }
        }
      }
    }

    return false;
  }

  /**
   * Check if two bounding boxes overlap
   */
  private boundsOverlap(a: BoundingBox, b: BoundingBox): boolean {
    return !(
      a.max.x < b.min.x ||
      a.min.x > b.max.x ||
      a.max.y < b.min.y ||
      a.min.y > b.max.y ||
      (a.max.z !== undefined &&
        b.max.z !== undefined &&
        (a.max.z < (b.min.z || 0) || a.min.z! > b.max.z))
    );
  }

  /**
   * Find objects within a radius
   */
  findNearby(
    position: Vector3,
    radius: number,
    filter?: (obj: PlacedObject) => boolean
  ): PlacedObject[] {
    const nearby: PlacedObject[] = [];
    const checked = new Set<string>();

    const cellRadius = Math.ceil(radius / this.cellSize);
    const centerCellX = Math.floor(position.x / this.cellSize);
    const centerCellY = Math.floor(position.y / this.cellSize);

    for (let cx = centerCellX - cellRadius; cx <= centerCellX + cellRadius; cx++) {
      for (let cy = centerCellY - cellRadius; cy <= centerCellY + cellRadius; cy++) {
        const key = `${cx},${cy}`;
        const objects = this.cells.get(key) || [];

        for (const obj of objects) {
          if (checked.has(obj.id)) continue;
          checked.add(obj.id);

          const distance = this.distance2D(position, obj.position);
          if (distance <= radius) {
            if (!filter || filter(obj)) {
              nearby.push(obj);
            }
          }
        }
      }
    }

    return nearby;
  }

  /**
   * Calculate 2D distance between two points
   */
  private distance2D(a: Vector3, b: Vector3): number {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * Get all objects of a specific type
   */
  getObjectsByType(type: string): PlacedObject[] {
    return Array.from(this.objects.values()).filter((obj) => obj.type === type);
  }

  /**
   * Get all objects
   */
  getAllObjects(): PlacedObject[] {
    return Array.from(this.objects.values());
  }

  /**
   * Clear the grid
   */
  clear(): void {
    this.cells.clear();
    this.objects.clear();
  }
}

/**
 * Procedural placement system with natural distribution rules
 */
export class ProceduralPlacement {
  private grid: SpatialGrid;
  private zoneMap: ZoneMap;
  private biomes: BiomeConfig[];

  constructor(zoneMap: ZoneMap, biomes: BiomeConfig[], cellSize: number = 10) {
    this.grid = new SpatialGrid(cellSize);
    this.zoneMap = zoneMap;
    this.biomes = biomes;
  }

  /**
   * Generate natural features (rivers, rocks, vegetation)
   */
  generateNaturalFeatures(): void {
    // For each cell in the map
    const { width, height } = this.zoneMap;

    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        const elevation = this.zoneMap.elevation[x][y];
        const moisture = this.zoneMap.moisture[x][y];
        const temperature = this.zoneMap.temperature[x][y];

        // Find matching biome
        const biome = this.getBiomeAtPoint(elevation, moisture, temperature);
        if (!biome) continue;

        // Place objects according to biome rules
        for (const objectConfig of biome.objects) {
          // Random sampling based on density
          if (Math.random() < objectConfig.density) {
            this.tryPlaceObject(
              objectConfig.type,
              { x, y, z: elevation },
              objectConfig.minSpacing,
              objectConfig.placementRules || []
            );
          }
        }
      }
    }
  }

  /**
   * Try to place an object at a position
   */
  private tryPlaceObject(
    type: string,
    position: Vector3,
    minSpacing: number,
    rules: PlacementRule[],
    maxAttempts: number = 5
  ): PlacedObject | null {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      // Add small random offset
      const offset = {
        x: position.x + (Math.random() - 0.5) * minSpacing,
        y: position.y + (Math.random() - 0.5) * minSpacing,
        z: position.z,
      };

      // Check placement rules
      if (!this.checkPlacementRules(offset, rules)) {
        continue;
      }

      // Create bounding box
      const bounds = this.getBoundsForType(type, offset);

      // Check collision
      if (this.grid.checkCollision(bounds)) {
        continue;
      }

      // Check minimum spacing
      const nearby = this.grid.findNearby(
        offset,
        minSpacing,
        (obj) => obj.type === type
      );
      if (nearby.length > 0) {
        continue;
      }

      // Place the object
      const obj: PlacedObject = {
        id: `${type}_${Date.now()}_${Math.random()}`,
        type,
        position: offset,
        bounds,
        rotation: Math.random() * Math.PI * 2,
        scale: { x: 1, y: 1, z: 1 },
      };

      this.grid.addObject(obj);
      return obj;
    }

    return null;
  }

  /**
   * Check if placement rules are satisfied
   */
  private checkPlacementRules(position: Vector3, rules: PlacementRule[]): boolean {
    for (const rule of rules) {
      let satisfied = false;

      switch (rule.type) {
        case 'near':
          if (rule.target) {
            const nearby = this.grid.findNearby(
              position,
              rule.distance?.max || 100,
              (obj) => obj.type === rule.target
            );
            satisfied = nearby.length > 0;
          }
          break;

        case 'avoid':
          if (rule.target) {
            const nearby = this.grid.findNearby(
              position,
              rule.distance?.min || 10,
              (obj) => obj.type === rule.target
            );
            satisfied = nearby.length === 0;
          }
          break;

        case 'elevation':
          if (rule.elevationRange) {
            const elevation = position.z || 0;
            satisfied =
              elevation >= rule.elevationRange.min &&
              elevation <= rule.elevationRange.max;
          }
          break;

        case 'slope':
          // Calculate slope from heightmap
          const slope = this.calculateSlope(position.x, position.y);
          if (rule.slopeRange) {
            satisfied =
              slope >= rule.slopeRange.min && slope <= rule.slopeRange.max;
          }
          break;

        default:
          satisfied = true;
      }

      if (rule.required && !satisfied) {
        return false;
      }
    }

    return true;
  }

  /**
   * Calculate slope at a position (in degrees)
   */
  private calculateSlope(x: number, y: number): number {
    const ix = Math.floor(x);
    const iy = Math.floor(y);

    if (
      ix < 0 ||
      iy < 0 ||
      ix >= this.zoneMap.width - 1 ||
      iy >= this.zoneMap.height - 1
    ) {
      return 0;
    }

    const elevation = this.zoneMap.elevation[ix][iy];
    const elevationRight = this.zoneMap.elevation[ix + 1][iy];
    const elevationUp = this.zoneMap.elevation[ix][iy + 1];

    const dx = elevationRight - elevation;
    const dy = elevationUp - elevation;

    const slope = Math.sqrt(dx * dx + dy * dy);
    return (Math.atan(slope) * 180) / Math.PI;
  }

  /**
   * Get biome at a specific point
   */
  private getBiomeAtPoint(
    elevation: number,
    moisture: number,
    temperature: number
  ): BiomeConfig | null {
    for (const biome of this.biomes) {
      if (
        elevation >= biome.elevation.min &&
        elevation <= biome.elevation.max &&
        moisture >= biome.moisture.min &&
        moisture <= biome.moisture.max &&
        temperature >= biome.temperature.min &&
        temperature <= biome.temperature.max
      ) {
        return biome;
      }
    }
    return null;
  }

  /**
   * Get bounding box for an object type
   */
  private getBoundsForType(type: string, position: Vector3): BoundingBox {
    // Default sizes - these should come from a config
    const sizes: Record<string, { width: number; height: number; depth: number }> =
      {
        tree: { width: 2, height: 5, depth: 2 },
        rock: { width: 1, height: 1, depth: 1 },
        shrub: { width: 0.5, height: 0.5, depth: 0.5 },
        house: { width: 10, height: 8, depth: 10 },
        npc: { width: 1, height: 2, depth: 1 },
      };

    const size = sizes[type] || { width: 1, height: 1, depth: 1 };

    return {
      min: {
        x: position.x - size.width / 2,
        y: position.y - size.depth / 2,
        z: position.z || 0,
      },
      max: {
        x: position.x + size.width / 2,
        y: position.y + size.depth / 2,
        z: (position.z || 0) + size.height,
      },
    };
  }

  /**
   * Get the spatial grid
   */
  getGrid(): SpatialGrid {
    return this.grid;
  }

  /**
   * Export placed objects
   */
  export(): PlacedObject[] {
    return this.grid.getAllObjects();
  }
}

/**
 * Generate a heightmap using Perlin-like noise
 */
export function generateHeightmap(
  width: number,
  height: number,
  scale: number = 50,
  octaves: number = 4
): number[][] {
  const map: number[][] = [];

  for (let x = 0; x < width; x++) {
    map[x] = [];
    for (let y = 0; y < height; y++) {
      let value = 0;
      let amplitude = 1;
      let frequency = 1;
      let maxValue = 0;

      for (let octave = 0; octave < octaves; octave++) {
        const sampleX = (x / scale) * frequency;
        const sampleY = (y / scale) * frequency;

        // Simple noise function (replace with actual Perlin/Simplex noise)
        const noise = Math.sin(sampleX) * Math.cos(sampleY);

        value += noise * amplitude;
        maxValue += amplitude;

        amplitude *= 0.5;
        frequency *= 2;
      }

      // Normalize to 0-1
      map[x][y] = (value / maxValue + 1) / 2;
    }
  }

  return map;
}
