"""
Project configuration and initialization
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project configuration"""

    # Project settings
    project_name: str
    project_root: Path
    template: str = "mmorpg"

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None

    # Generation settings
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.8
    max_level: int = 100

    # Image generation
    image_model: str = "dall-e-3"
    image_quality: str = "hd"
    enable_quality_check: bool = True

    # Voice generation
    voice_model: str = "eleven_multilingual_v2"
    voice_stability: float = 0.5
    voice_similarity_boost: float = 0.75
    voice_style: float = 0.0
    voice_use_speaker_boost: bool = True

    # Storage
    content_dir: Path = Field(default_factory=lambda: Path("assets/game_content"))
    images_dir: Path = Field(default_factory=lambda: Path("assets/images"))
    audio_dir: Path = Field(default_factory=lambda: Path("assets/audio"))
    exports_dir: Path = Field(default_factory=lambda: Path("exports"))

    class Config:
        arbitrary_types_allowed = True


def load_config(project_root: Optional[Path] = None) -> ProjectConfig:
    """Load project configuration"""
    if project_root is None:
        project_root = Path.cwd()

    config_file = project_root / ".gamedatagen" / "config.yaml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"No GameDataGen project found in {project_root}\n"
            "Run 'gamedatagen init <project-name>' to create a new project"
        )

    with open(config_file) as f:
        data = yaml.safe_load(f)

    # Convert string paths to Path objects
    if "project_root" in data:
        data["project_root"] = Path(data["project_root"])
    else:
        data["project_root"] = project_root

    if "content_dir" in data:
        data["content_dir"] = project_root / data["content_dir"]
    if "images_dir" in data:
        data["images_dir"] = project_root / data["images_dir"]
    if "audio_dir" in data:
        data["audio_dir"] = project_root / data["audio_dir"]
    if "exports_dir" in data:
        data["exports_dir"] = project_root / data["exports_dir"]

    return ProjectConfig(**data)


def save_config(config: ProjectConfig) -> None:
    """Save project configuration"""
    config_file = config.project_root / ".gamedatagen" / "config.yaml"

    data = config.model_dump()

    # Convert Path objects to strings
    data["project_root"] = str(data["project_root"])
    data["content_dir"] = str(Path(data["content_dir"]).relative_to(config.project_root))
    data["images_dir"] = str(Path(data["images_dir"]).relative_to(config.project_root))
    data["audio_dir"] = str(Path(data["audio_dir"]).relative_to(config.project_root))
    data["exports_dir"] = str(Path(data["exports_dir"]).relative_to(config.project_root))

    with open(config_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def init_project(
    project_path: Path,
    template: str = "mmorpg",
    include_examples: bool = True,
) -> None:
    """Initialize a new GameDataGen project"""

    project_path.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    directories = [
        ".gamedatagen",
        ".gamedatagen/schemas",
        "assets/game_content/quests",
        "assets/game_content/quests/_templates",
        "assets/game_content/npcs",
        "assets/game_content/npcs/_templates",
        "assets/game_content/items",
        "assets/game_content/items/_templates",
        "assets/game_content/enemies",
        "assets/game_content/enemies/_templates",
        "assets/game_content/zones",
        "assets/game_content/zones/_templates",
        "assets/game_content/events",
        "assets/game_content/events/_templates",
        "assets/images/items",
        "assets/images/characters",
        "assets/images/enemies",
        "assets/images/environments",
        "assets/audio/dialogue",
        "assets/audio/npcs",
        "assets/audio/quests",
        "exports/unity",
        "exports/unreal",
        "exports/godot",
        "exports/json",
    ]

    for dir_path in directories:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Create config file
    config = ProjectConfig(
        project_name=project_path.name,
        project_root=project_path,
        template=template,
        content_dir=project_path / "assets/game_content",
        images_dir=project_path / "assets/images",
        audio_dir=project_path / "assets/audio",
        exports_dir=project_path / "exports",
    )
    save_config(config)

    # Create README
    readme_content = f"""# {project_path.name}

AI-generated game content using GameDataGen.

## Setup

1. Configure your API keys in `.gamedatagen/config.yaml`
2. Review and customize schemas in `.gamedatagen/schemas/`

## Usage

Generate content:
```bash
gamedatagen generate quests --count 10
gamedatagen generate npcs --zone "Forest" --count 5
gamedatagen generate items --level-range "1-10" --images
```

Edit content:
```bash
gamedatagen edit quest quest_001 --update '{{"difficulty": "hard"}}'
```

Start API server:
```bash
gamedatagen serve --port 8000
```

View project status:
```bash
gamedatagen status
```

## Project Structure

```
assets/
├── game_content/     # Generated JSON files
│   ├── quests/
│   ├── npcs/
│   ├── items/
│   └── ...
└── images/          # Generated images
    ├── items/
    ├── characters/
    └── ...

exports/             # Game engine exports
├── unity/
├── unreal/
└── godot/
```

## API Usage

```bash
# Start server
gamedatagen serve

# Generate via API
curl -X POST "http://localhost:8000/generate/quests?count=5"

# Get entities
curl "http://localhost:8000/entities/quests"

# View docs
open http://localhost:8000/docs
```
"""

    (project_path / "README.md").write_text(readme_content)

    # Create .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# API keys (IMPORTANT!)
.gamedatagen/config.yaml

# Generated content (optional - commit if you want to version control)
# assets/game_content/
# assets/images/

# Exports
exports/

# IDE
.vscode/
.idea/
*.swp
*.swo
"""

    (project_path / ".gitignore").write_text(gitignore_content)

    # Copy template schemas if they exist
    if include_examples:
        _create_example_schemas(project_path, template)

    # Create example templates
    _create_templates(project_path)


def _create_example_schemas(project_path: Path, template: str) -> None:
    """Create example schema files"""

    schemas_dir = project_path / ".gamedatagen" / "schemas"

    # Quest schema
    quest_schema = {
        "name": "Quest",
        "description": "A quest or mission for players",
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "quest_giver": {"type": "string"},
                "level_requirement": {"type": "integer"},
                "objectives": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "rewards": {
                    "type": "object",
                    "properties": {
                        "xp": {"type": "integer"},
                        "gold": {"type": "integer"},
                        "items": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "type": {"type": "string", "enum": ["main", "side", "daily", "event"]},
                "zone": {"type": "string"}
            },
            "required": ["id", "name", "description", "level_requirement"]
        }
    }

    (schemas_dir / "quest.yaml").write_text(yaml.dump(quest_schema))

    # NPC schema
    npc_schema = {
        "name": "NPC",
        "description": "A non-player character",
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "race": {"type": "string"},
                "class": {"type": "string"},
                "level": {"type": "integer"},
                "personality": {"type": "string"},
                "role": {"type": "string", "enum": ["merchant", "quest_giver", "trainer", "guard"]},
                "dialogue": {"type": "array", "items": {"type": "string"}},
                "voice_id": {"type": "string"},
                "voice_metadata": {
                    "type": "object",
                    "properties": {
                        "audio_files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "dialogue_index": {"type": "integer"},
                                    "filepath": {"type": "string"},
                                    "generated_at": {"type": "string"}
                                }
                            }
                        },
                        "last_generated": {"type": "string"}
                    }
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "zone": {"type": "string"},
                        "position": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "z": {"type": "number"}
                            }
                        }
                    }
                }
            },
            "required": ["id", "name", "race", "class", "level"]
        }
    }

    (schemas_dir / "npc.yaml").write_text(yaml.dump(npc_schema))

    # Item schema
    item_schema = {
        "name": "Item",
        "description": "A game item (weapon, armor, consumable, etc.)",
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string", "enum": ["weapon", "armor", "consumable", "quest_item"]},
                "rarity": {"type": "string", "enum": ["common", "uncommon", "rare", "epic", "legendary"]},
                "level_requirement": {"type": "integer"},
                "description": {"type": "string"},
                "stats": {"type": "object"},
                "value": {"type": "integer"}
            },
            "required": ["id", "name", "type", "rarity"]
        }
    }

    (schemas_dir / "item.yaml").write_text(yaml.dump(item_schema))


def _create_templates(project_path: Path) -> None:
    """Create template files for each entity type"""

    # Quest template
    quest_template = {
        "_template": True,
        "_description": "Copy this to create new quests manually",
        "id": "quest_xxx",
        "name": "Quest Name",
        "description": "Quest description",
        "quest_giver": "npc_id",
        "level_requirement": 1,
        "objectives": [
            "Objective 1",
            "Objective 2"
        ],
        "rewards": {
            "xp": 1000,
            "gold": 50,
            "items": []
        },
        "type": "side",
        "zone": "zone_id"
    }

    template_path = project_path / "assets/game_content/quests/_templates/quest_template.json"
    import json
    template_path.write_text(json.dumps(quest_template, indent=2))

    # NPC template
    npc_template = {
        "_template": True,
        "_description": "Copy this to create new NPCs manually",
        "id": "npc_xxx",
        "name": "NPC Name",
        "race": "Human",
        "class": "Merchant",
        "level": 1,
        "personality": "Friendly",
        "role": "merchant",
        "dialogue": ["Hello, traveler!"],
        "location": {
            "zone": "zone_id",
            "position": {"x": 0, "y": 0, "z": 0}
        }
    }

    template_path = project_path / "assets/game_content/npcs/_templates/npc_template.json"
    template_path.write_text(json.dumps(npc_template, indent=2))
