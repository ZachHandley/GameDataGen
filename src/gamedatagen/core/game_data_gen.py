"""
Main GameDataGen orchestrator

Ties together all systems for complete game content generation.
"""

import json
from pathlib import Path
from typing import Any

from gamedatagen.config import ProjectConfig
from gamedatagen.core.generation_engine import GenerationContext, GenerationEngine
from gamedatagen.core.knowledge_graph import EntityReference, KnowledgeGraph, Triplet
from gamedatagen.core.leveling_system import LevelingSystem
from gamedatagen.core.schema_registry import SchemaRegistry
from gamedatagen.core.spatial_system import BoundingBox, SpatialGrid, Vector3
from gamedatagen.utils.image_gen import ImageGenerator


class GameDataGen:
    """Main orchestrator for game content generation"""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config

        # Initialize core systems
        self.schema_registry = SchemaRegistry()
        self.knowledge_graph = KnowledgeGraph()
        self.leveling_system = LevelingSystem(max_level=config.max_level)

        # Spatial grid (1000x1000x1000 world)
        self.spatial_grid = SpatialGrid(
            bounds=BoundingBox(
                min=Vector3(x=-500, y=0, z=-500),
                max=Vector3(x=500, y=100, z=500),
            )
        )

        # Generation engine
        self.generation_engine = GenerationEngine(
            model=config.default_model,
            temperature=config.temperature,
            schema_registry=self.schema_registry,
            knowledge_graph=self.knowledge_graph,
        )

        # Image generator
        self.image_generator = ImageGenerator(api_key=config.openai_api_key)

        # Load schemas
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load schemas from project"""
        schemas_dir = self.config.project_root / ".gamedatagen" / "schemas"
        if schemas_dir.exists():
            count = self.schema_registry.load_schemas_from_directory(schemas_dir)
            print(f"Loaded {count} schemas")

    async def generate(
        self,
        entity_type: str,
        count: int = 1,
        context: str | None = None,
        style: str | None = None,
        min_level: int | None = None,
        max_level: int | None = None,
        zone: str | None = None,
        generate_images: bool = False,
        quality_check: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Generate game content

        Args:
            entity_type: Type of entity to generate
            count: Number to generate
            context: Additional context
            style: Generation style
            min_level: Minimum level
            max_level: Maximum level
            zone: Zone/area
            generate_images: Generate images for entities
            quality_check: Enable image quality control

        Returns:
            List of generated entities with metadata
        """
        # Build generation context
        gen_context = GenerationContext(
            style=style,
            custom_context=context,
        )

        # Build specifications
        specifications: dict[str, Any] = {}
        if min_level:
            specifications["min_level"] = min_level
        if max_level:
            specifications["max_level"] = max_level
        if zone:
            specifications["zone"] = zone

        # Generate entities
        entities = await self.generation_engine.generate_batch(
            entity_type=entity_type,
            count=count,
            context=gen_context,
            specifications=specifications,
        )

        # Save entities and optionally generate images
        results = []
        content_dir = self.config.content_dir / entity_type.lower() + "s"
        images_dir = self.config.images_dir / entity_type.lower() + "s"

        content_dir.mkdir(parents=True, exist_ok=True)

        for i, entity in enumerate(entities):
            # Ensure ID
            if "id" not in entity:
                entity["id"] = f"{entity_type.lower()}_{i:04d}"

            # Save entity JSON
            entity_file = content_dir / f"{entity['id']}.json"
            entity_file.write_text(json.dumps(entity, indent=2))

            result = {
                **entity,
                "filepath": str(entity_file),
            }

            # Generate image if requested
            if generate_images:
                image_result = await self.image_generator.generate_and_save(
                    entity_type=entity_type,
                    entity_data=entity,
                    output_dir=images_dir,
                    style=style,
                    quality_check=quality_check,
                )
                result["image"] = image_result

            results.append(result)

        return results

    async def edit(
        self,
        entity_type: str,
        entity_id: str,
        updates: dict[str, Any],
        regenerate_dependencies: bool = False,
    ) -> dict[str, Any]:
        """
        Edit existing entity

        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            updates: Updates to apply
            regenerate_dependencies: Regenerate dependent entities

        Returns:
            Edit result with updated entity
        """
        # Load entity
        entity = self.get_entity(entity_type, entity_id)
        if not entity:
            raise ValueError(f"Entity not found: {entity_type}/{entity_id}")

        # Apply edits via generation engine
        updated_entity = await self.generation_engine.regenerate_with_edits(
            entity_type=entity_type,
            original_entity=entity,
            edits=updates,
        )

        # Save updated entity
        content_dir = self.config.content_dir / entity_type.lower() + "s"
        entity_file = content_dir / f"{entity_id}.json"
        entity_file.write_text(json.dumps(updated_entity, indent=2))

        result: dict[str, Any] = {
            "entity": updated_entity,
            "filepath": str(entity_file),
        }

        # Regenerate dependencies if requested
        if regenerate_dependencies:
            # Find dependent entities from knowledge graph
            ref = EntityReference(type=entity_type, id=entity_id)
            dependent_triplets = self.knowledge_graph.find(object=ref)

            regenerated = []
            for triplet in dependent_triplets:
                # TODO: Regenerate dependent entity
                pass

            result["regenerated"] = regenerated

        return result

    def get_entity(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        """Get entity by ID"""
        content_dir = self.config.content_dir / entity_type.lower() + "s"
        entity_file = content_dir / f"{entity_id}.json"

        if not entity_file.exists():
            return None

        return json.loads(entity_file.read_text())

    def list_entities(
        self,
        entity_type: str,
        zone: str | None = None,
        level_min: int | None = None,
        level_max: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List entities with filtering"""
        content_dir = self.config.content_dir / entity_type.lower() + "s"

        if not content_dir.exists():
            return []

        entities = []
        for entity_file in content_dir.glob("*.json"):
            entity = json.loads(entity_file.read_text())

            # Filter
            if zone and entity.get("zone") != zone:
                continue

            entity_level = entity.get("level") or entity.get("level_requirement")
            if level_min and entity_level and entity_level < level_min:
                continue
            if level_max and entity_level and entity_level > level_max:
                continue

            entities.append(entity)

        # Pagination
        return entities[offset : offset + limit]

    def delete_entity(self, entity_type: str, entity_id: str) -> None:
        """Delete entity"""
        content_dir = self.config.content_dir / entity_type.lower() + "s"
        entity_file = content_dir / f"{entity_id}.json"

        if entity_file.exists():
            entity_file.unlink()

        # Remove from knowledge graph
        ref = EntityReference(type=entity_type, id=entity_id)
        self.knowledge_graph.remove_entity(ref)

    def query_knowledge_graph(
        self,
        entity_type: str | None = None,
        predicate: str | None = None,
    ) -> list[Triplet]:
        """Query knowledge graph"""
        if entity_type:
            # Find all triplets with this entity type
            return [
                t
                for t in self.knowledge_graph.triplets
                if t.subject.type == entity_type or t.object.type == entity_type
            ]
        elif predicate:
            return self.knowledge_graph.find(predicate=predicate)
        else:
            return self.knowledge_graph.triplets

    async def generate_image(
        self,
        entity_type: str,
        entity_id: str,
        quality_check: bool = False,
    ) -> dict[str, Any]:
        """Generate image for existing entity"""
        entity = self.get_entity(entity_type, entity_id)
        if not entity:
            raise ValueError(f"Entity not found: {entity_type}/{entity_id}")

        images_dir = self.config.images_dir / entity_type.lower() + "s"

        return await self.image_generator.generate_and_save(
            entity_type=entity_type,
            entity_data=entity,
            output_dir=images_dir,
            quality_check=quality_check,
        )

    def export(self, format: str, output_dir: Path | None = None) -> Path:
        """Export content to game engine format"""
        if output_dir is None:
            output_dir = self.config.exports_dir / format

        output_dir.mkdir(parents=True, exist_ok=True)

        # Import exporters
        from gamedatagen.exporters.bevy import BevyExporter
        from gamedatagen.exporters.json_exporter import JSONExporter

        if format == "bevy" or format == "rust":
            # Bevy/Rust export (RON format)
            exporter = BevyExporter(self.config.content_dir)
            exporter.export(output_dir, format="ron")
        elif format == "bevy-json":
            # Bevy with JSON format
            exporter = BevyExporter(self.config.content_dir)
            exporter.export(output_dir, format="json")
        elif format == "json":
            # Simple JSON export
            exporter = JSONExporter(self.config.content_dir)
            exporter.export(output_dir)
        else:
            # Fallback to simple JSON copy
            import shutil

            shutil.copytree(self.config.content_dir, output_dir / "content", dirs_exist_ok=True)

        return output_dir

    def get_stats(self) -> dict[str, Any]:
        """Get project statistics"""
        stats: dict[str, Any] = {
            "entities": {},
            "knowledge_graph": self.knowledge_graph.stats(),
            "storage": {},
        }

        # Count entities
        if self.config.content_dir.exists():
            for entity_dir in self.config.content_dir.iterdir():
                if entity_dir.is_dir():
                    entity_type = entity_dir.name
                    count = len(list(entity_dir.glob("*.json")))
                    stats["entities"][entity_type] = count

        # Storage stats
        total_size = 0
        image_count = 0

        if self.config.images_dir.exists():
            for image_file in self.config.images_dir.rglob("*.png"):
                total_size += image_file.stat().st_size
                image_count += 1

        stats["storage"] = {
            "images": image_count,
            "total_size_mb": total_size / (1024 * 1024),
        }

        return stats

    def visualize(self, graph_type: str = "all") -> Path:
        """Generate knowledge graph visualization"""
        from gamedatagen.visualization import visualize_knowledge_graph

        output_file = self.config.project_root / "knowledge_graph.html"
        return visualize_knowledge_graph(self.knowledge_graph, output_file)
