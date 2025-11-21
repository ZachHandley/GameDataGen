"""Simple JSON exporter"""

import json
import shutil
from pathlib import Path


class JSONExporter:
    """Export game content as JSON"""

    def __init__(self, content_dir: Path) -> None:
        self.content_dir = content_dir

    def export(self, output_dir: Path) -> None:
        """Export all content to JSON"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy all JSON files
        shutil.copytree(self.content_dir, output_dir / "content", dirs_exist_ok=True)

        # Create consolidated files per entity type
        for entity_dir in self.content_dir.iterdir():
            if not entity_dir.is_dir() or entity_dir.name.startswith("_"):
                continue

            entity_type = entity_dir.name
            entities = []

            for entity_file in entity_dir.glob("*.json"):
                if entity_file.stem.startswith("_"):
                    continue
                entities.append(json.loads(entity_file.read_text()))

            # Write consolidated file
            if entities:
                consolidated_file = output_dir / f"{entity_type}_all.json"
                consolidated_file.write_text(json.dumps(entities, indent=2))
