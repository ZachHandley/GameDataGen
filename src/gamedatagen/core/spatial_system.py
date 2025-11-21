"""
Spatial System for collision detection and procedural placement

Handles 3D positioning, collision detection, and natural object placement.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel


class Vector3(BaseModel):
    """3D vector"""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def distance_to(self, other: "Vector3") -> float:
        """Calculate distance to another vector"""
        return np.sqrt(
            (self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2
        )

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(x=self.x + other.x, y=self.y + other.y, z=self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(x=self.x - other.x, y=self.y - other.y, z=self.z - other.z)


class BoundingBox(BaseModel):
    """3D bounding box"""

    min: Vector3
    max: Vector3

    def contains(self, point: Vector3) -> bool:
        """Check if point is inside bounding box"""
        return (
            self.min.x <= point.x <= self.max.x
            and self.min.y <= point.y <= self.max.y
            and self.min.z <= point.z <= self.max.z
        )

    def intersects(self, other: "BoundingBox") -> bool:
        """Check if this box intersects another"""
        return (
            self.min.x <= other.max.x
            and self.max.x >= other.min.x
            and self.min.y <= other.max.y
            and self.max.y >= other.min.y
            and self.min.z <= other.max.z
            and self.max.z >= other.min.z
        )


class PlacedObject(BaseModel):
    """Object placed in 3D space"""

    id: str
    entity_type: str
    position: Vector3
    bounds: BoundingBox
    metadata: Dict[str, Any] = {}


class PlacementRule(BaseModel):
    """Rule for procedural placement"""

    name: str
    biome: Optional[str] = None  # e.g., "forest", "desert"
    near_water: bool = False
    avoid_slopes: bool = False
    min_distance: float = 5.0  # Minimum distance from other objects
    max_distance: Optional[float] = None
    height_range: Optional[Tuple[float, float]] = None


class SpatialGrid:
    """3D spatial grid for collision detection and placement"""

    def __init__(self, bounds: BoundingBox, cell_size: float = 10.0) -> None:
        self.bounds = bounds
        self.cell_size = cell_size
        self.objects: Dict[str, PlacedObject] = {}

        # Spatial hash for fast queries
        self.grid: Dict[Tuple[int, int, int], List[str]] = {}

    def add_object(self, obj: PlacedObject) -> bool:
        """
        Add object to grid

        Returns:
            True if added successfully, False if collision detected
        """
        # Check collision
        if self.check_collision(obj.bounds, exclude_id=obj.id):
            return False

        # Add to objects
        self.objects[obj.id] = obj

        # Add to spatial hash
        cells = self._get_cells(obj.bounds)
        for cell in cells:
            if cell not in self.grid:
                self.grid[cell] = []
            self.grid[cell].append(obj.id)

        return True

    def remove_object(self, obj_id: str) -> bool:
        """Remove object from grid"""
        if obj_id not in self.objects:
            return False

        obj = self.objects[obj_id]

        # Remove from spatial hash
        cells = self._get_cells(obj.bounds)
        for cell in cells:
            if cell in self.grid and obj_id in self.grid[cell]:
                self.grid[cell].remove(obj_id)
                if not self.grid[cell]:
                    del self.grid[cell]

        # Remove from objects
        del self.objects[obj_id]
        return True

    def check_collision(
        self, bounds: BoundingBox, exclude_id: Optional[str] = None
    ) -> bool:
        """Check if bounds collide with any existing objects"""
        # Get potentially colliding objects from spatial hash
        cells = self._get_cells(bounds)
        candidates = set()

        for cell in cells:
            if cell in self.grid:
                candidates.update(self.grid[cell])

        # Check actual collision
        for obj_id in candidates:
            if obj_id == exclude_id:
                continue

            obj = self.objects[obj_id]
            if bounds.intersects(obj.bounds):
                return True

        return False

    def find_nearby(
        self,
        position: Vector3,
        radius: float,
        entity_type: Optional[str] = None,
    ) -> List[PlacedObject]:
        """Find objects within radius of position"""
        # Create search bounds
        search_bounds = BoundingBox(
            min=Vector3(x=position.x - radius, y=position.y - radius, z=position.z - radius),
            max=Vector3(x=position.x + radius, y=position.y + radius, z=position.z + radius),
        )

        # Get candidates from spatial hash
        cells = self._get_cells(search_bounds)
        candidates = set()

        for cell in cells:
            if cell in self.grid:
                candidates.update(self.grid[cell])

        # Filter by actual distance
        results = []
        for obj_id in candidates:
            obj = self.objects[obj_id]

            # Filter by type if specified
            if entity_type and obj.entity_type != entity_type:
                continue

            # Check distance
            distance = position.distance_to(obj.position)
            if distance <= radius:
                results.append(obj)

        return results

    def find_placement(
        self,
        entity_id: str,
        entity_type: str,
        size: Vector3,
        rule: PlacementRule,
        max_attempts: int = 100,
    ) -> Optional[Vector3]:
        """
        Find valid placement for an object using placement rules

        Args:
            entity_id: Object ID
            entity_type: Object type
            size: Object size (bounding box dimensions)
            rule: Placement rule
            max_attempts: Maximum placement attempts

        Returns:
            Valid position or None if no placement found
        """
        rng = np.random.RandomState()

        for _ in range(max_attempts):
            # Generate random position within bounds
            x = rng.uniform(self.bounds.min.x, self.bounds.max.x)
            z = rng.uniform(self.bounds.min.z, self.bounds.max.z)

            # Set Y based on height range
            if rule.height_range:
                y = rng.uniform(rule.height_range[0], rule.height_range[1])
            else:
                y = rng.uniform(self.bounds.min.y, self.bounds.max.y)

            position = Vector3(x=x, y=y, z=z)

            # Create bounding box
            bounds = BoundingBox(
                min=position - Vector3(x=size.x / 2, y=0, z=size.z / 2),
                max=position + Vector3(x=size.x / 2, y=size.y, z=size.z / 2),
            )

            # Check collision
            if self.check_collision(bounds):
                continue

            # Check min distance rule
            if rule.min_distance > 0:
                nearby = self.find_nearby(position, rule.min_distance)
                if nearby:
                    continue

            # Check max distance rule
            if rule.max_distance is not None:
                nearby = self.find_nearby(position, rule.max_distance)
                if not nearby:
                    continue

            # Valid placement found
            return position

        # No valid placement found
        return None

    def procedural_placement(
        self,
        entity_type: str,
        count: int,
        size: Vector3,
        rule: PlacementRule,
    ) -> List[PlacedObject]:
        """
        Procedurally place multiple objects

        Args:
            entity_type: Type of objects to place
            count: Number of objects
            size: Object size
            rule: Placement rule

        Returns:
            List of placed objects
        """
        placed = []

        for i in range(count):
            entity_id = f"{entity_type}_{i:04d}"

            position = self.find_placement(
                entity_id=entity_id,
                entity_type=entity_type,
                size=size,
                rule=rule,
            )

            if position is None:
                print(f"Warning: Could not place {entity_id} after max attempts")
                continue

            # Create placed object
            bounds = BoundingBox(
                min=position - Vector3(x=size.x / 2, y=0, z=size.z / 2),
                max=position + Vector3(x=size.x / 2, y=size.y, z=size.z / 2),
            )

            obj = PlacedObject(
                id=entity_id,
                entity_type=entity_type,
                position=position,
                bounds=bounds,
                metadata={"rule": rule.name, "biome": rule.biome},
            )

            if self.add_object(obj):
                placed.append(obj)

        return placed

    def _get_cells(self, bounds: BoundingBox) -> List[Tuple[int, int, int]]:
        """Get grid cells that overlap with bounds"""
        min_cell_x = int(np.floor(bounds.min.x / self.cell_size))
        max_cell_x = int(np.floor(bounds.max.x / self.cell_size))
        min_cell_y = int(np.floor(bounds.min.y / self.cell_size))
        max_cell_y = int(np.floor(bounds.max.y / self.cell_size))
        min_cell_z = int(np.floor(bounds.min.z / self.cell_size))
        max_cell_z = int(np.floor(bounds.max.z / self.cell_size))

        cells = []
        for x in range(min_cell_x, max_cell_x + 1):
            for y in range(min_cell_y, max_cell_y + 1):
                for z in range(min_cell_z, max_cell_z + 1):
                    cells.append((x, y, z))

        return cells

    def get_stats(self) -> Dict[str, Any]:
        """Get spatial grid statistics"""
        return {
            "total_objects": len(self.objects),
            "grid_cells_used": len(self.grid),
            "bounds": {
                "min": self.bounds.min.model_dump(),
                "max": self.bounds.max.model_dump(),
            },
            "cell_size": self.cell_size,
        }
