# 🎮 GameDataGen

**AI-powered game content generation framework** - Generate complete MMORPG worlds with NPCs, quests, items, enemies, and more using LLMs.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![UV](https://img.shields.io/badge/UV-tool-orange.svg)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🤖 **Multi-Model Support** - LiteLLM integration supports 100+ LLMs (OpenAI, Anthropic, Gemini, local models)
- 📊 **Dynamic Schemas** - Load any JSON/YAML schema at runtime, auto-converts to Pydantic
- 🕸️ **Knowledge Graph** - Rich entity relationships with triplets (subject, predicate, object, metadata)
- 📈 **XP Budgeting** - Ensures players reach max level through available content
- 🎯 **Spatial System** - 3D collision detection and procedural placement
- 🖼️ **Image Generation** - DALL-E integration with AI-powered quality control
- 🦀 **Bevy/Rust Export** - RON format for Bevy game engine
- 🌐 **REST API** - FastAPI server with local storage
- 📊 **Visualization** - Interactive knowledge graph visualization
- ⚡ **UV Tool** - Instant installs with `uvx gamedatagen`

## 🚀 Quick Start

### Installation

```bash
# Install as UV tool (recommended)
uvx gamedatagen init my-rpg-game

# Or install globally
uv tool install gamedatagen
gamedatagen init my-rpg-game
```

### Initialize Project

```bash
gamedatagen init my-rpg-game
cd my-rpg-game

# Edit config with your API keys
vim .gamedatagen/config.yaml
```

### Generate Content

```bash
# Generate quests
gamedatagen generate quests --count 10 --style dark-fantasy

# Generate NPCs with images
gamedatagen generate npcs --zone "Shadowmoon Forest" --count 5 --images --quality-check

# Generate items for specific level range
gamedatagen generate items --level-range "50-60" --count 20
```

### Export for Bevy (Rust)

```bash
# Export for Bevy - RON format
gamedatagen export bevy --output ./bevy-assets

# Export for Bevy - JSON format
gamedatagen export bevy-json
```

### Visualize Knowledge Graph

```bash
gamedatagen visualize
# Opens knowledge_graph.html with interactive visualization
```

### Start API Server

```bash
gamedatagen serve --port 8000
# API docs at http://localhost:8000/docs
```

## 🦀 Bevy Integration

GameDataGen exports content specifically for [Bevy game engine](https://bevyengine.org/) in Rust.

### Export Process

```bash
gamedatagen export bevy
```

This generates:
- `entities.rs` - Complete Rust struct definitions with Bevy components
- `*.ron` - Data files in RON (Rusty Object Notation)
- `README.md` - Comprehensive integration guide
- Asset manifest for Bevy asset loader

### In Your Bevy Project

1. **Add to Cargo.toml:**

```toml
[dependencies]
bevy = "0.14"
serde = { version = "1.0", features = ["derive"] }
```

2. **Copy generated files:**

```bash
cp exports/bevy/entities.rs src/
cp exports/bevy/*.ron assets/
```

3. **Load assets:**

```rust
use bevy::prelude::*;
use crate::entities::*;

fn setup(asset_server: Res<AssetServer>) {
    let quests: Handle<QuestCollection> = asset_server.load("quests.ron");
    let npcs: Handle<NPCCollection> = asset_server.load("npcs.ron");
    let items: Handle<ItemCollection> = asset_server.load("items.ron");
}
```

### Example RON Format

```ron
// quests.ron
[
  (
    id: "quest_001",
    name: "The Dragon's Lair",
    description: "Investigate the ancient dragon's lair",
    level_requirement: 50,
    objectives: [
      "Enter the dragon's lair",
      "Defeat the ancient dragon"
    ],
    rewards: (
      xp: 50000,
      gold: 1000,
      items: ["legendary_sword"]
    ),
    quest_type: Main,
    zone: Some("Mountains")
  )
]
```

## 📖 Documentation

See [full documentation](https://github.com/ZachHandley/GameDataGen/docs) for:
- CLI commands reference
- API endpoints
- Custom schema creation
- Knowledge graph usage
- Image generation guide
- Bevy integration examples

## 🐳 Docker

```bash
# Build
docker build -t gamedatagen .

# Run API server
docker run -p 8000:8000 -v $(pwd)/my-project:/project \
  gamedatagen gamedatagen serve --host 0.0.0.0

# Run CLI
docker run -v $(pwd):/project gamedatagen \
  gamedatagen generate quests --count 10
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

Built with ❤️ for game developers
