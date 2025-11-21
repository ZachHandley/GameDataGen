"""
GameDataGen - AI-powered game content generation framework

Generate complete game worlds with NPCs, quests, items, enemies, and more
using LLMs (LiteLLM multi-model support).
"""

__version__ = "0.1.0"

from gamedatagen.core.game_data_gen import GameDataGen
from gamedatagen.core.schema_registry import SchemaRegistry
from gamedatagen.core.knowledge_graph import KnowledgeGraph, Triplet
from gamedatagen.core.leveling_system import LevelingSystem
from gamedatagen.core.spatial_system import SpatialGrid, Vector3

__all__ = [
    "GameDataGen",
    "SchemaRegistry",
    "KnowledgeGraph",
    "Triplet",
    "LevelingSystem",
    "SpatialGrid",
    "Vector3",
    "__version__",
]
