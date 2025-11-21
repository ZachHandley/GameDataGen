"""
Leveling System for XP budgeting and content scaling

Ensures players can reach max level through available content.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


class XPCurve(BaseModel):
    """XP curve configuration"""

    curve_type: str = "exponential"  # exponential, linear, logarithmic
    base_xp: int = 100
    exponent: float = 1.5
    level_multiplier: float = 1.0


class ContentBudget(BaseModel):
    """Content distribution for XP budgeting"""

    main_quests_percent: float = 0.35
    side_quests_percent: float = 0.25
    dungeons_percent: float = 0.20
    events_percent: float = 0.10
    grinding_percent: float = 0.10


class LevelingSystem:
    """XP budgeting and content scaling system"""

    def __init__(
        self,
        max_level: int = 100,
        xp_curve: Optional[XPCurve] = None,
        content_budget: Optional[ContentBudget] = None,
    ) -> None:
        self.max_level = max_level
        self.xp_curve = xp_curve or XPCurve()
        self.content_budget = content_budget or ContentBudget()

        # Calculate XP per level
        self.xp_per_level = self._calculate_xp_table()
        self.total_xp_needed = sum(self.xp_per_level.values())

    def _calculate_xp_table(self) -> Dict[int, int]:
        """Calculate XP needed for each level"""
        xp_table = {}

        if self.xp_curve.curve_type == "exponential":
            curve_fn = self._exponential_curve
        elif self.xp_curve.curve_type == "linear":
            curve_fn = self._linear_curve
        elif self.xp_curve.curve_type == "logarithmic":
            curve_fn = self._logarithmic_curve
        else:
            curve_fn = self._exponential_curve

        for level in range(1, self.max_level + 1):
            xp_table[level] = curve_fn(level)

        return xp_table

    def _exponential_curve(self, level: int) -> int:
        """Exponential XP curve (gets harder as you level)"""
        return int(
            self.xp_curve.base_xp
            * (level ** self.xp_curve.exponent)
            * self.xp_curve.level_multiplier
        )

    def _linear_curve(self, level: int) -> int:
        """Linear XP curve (constant increase)"""
        return int(self.xp_curve.base_xp * level * self.xp_curve.level_multiplier)

    def _logarithmic_curve(self, level: int) -> int:
        """Logarithmic XP curve (easier at higher levels)"""
        import math

        return int(
            self.xp_curve.base_xp
            * math.log(level + 1)
            * level
            * self.xp_curve.level_multiplier
        )

    def get_level_range_xp(self, min_level: int, max_level: int) -> int:
        """Get total XP needed for a level range"""
        return sum(self.xp_per_level[level] for level in range(min_level, max_level + 1))

    def calculate_content_requirements(
        self,
    ) -> Dict[str, Dict[str, int]]:
        """
        Calculate how much content is needed to reach max level

        Returns budget breakdown per content type.
        """
        budget = {}

        # Main quests
        main_quest_xp = int(self.total_xp_needed * self.content_budget.main_quests_percent)
        avg_main_quest_xp = 500  # Configurable
        budget["main_quests"] = {
            "total_xp": main_quest_xp,
            "count": main_quest_xp // avg_main_quest_xp,
            "avg_xp": avg_main_quest_xp,
        }

        # Side quests
        side_quest_xp = int(self.total_xp_needed * self.content_budget.side_quests_percent)
        avg_side_quest_xp = 200
        budget["side_quests"] = {
            "total_xp": side_quest_xp,
            "count": side_quest_xp // avg_side_quest_xp,
            "avg_xp": avg_side_quest_xp,
        }

        # Dungeons
        dungeon_xp = int(self.total_xp_needed * self.content_budget.dungeons_percent)
        avg_dungeon_xp = 1000
        budget["dungeons"] = {
            "total_xp": dungeon_xp,
            "count": dungeon_xp // avg_dungeon_xp,
            "avg_xp": avg_dungeon_xp,
        }

        # Events
        event_xp = int(self.total_xp_needed * self.content_budget.events_percent)
        avg_event_xp = 300
        budget["events"] = {
            "total_xp": event_xp,
            "count": event_xp // avg_event_xp,
            "avg_xp": avg_event_xp,
        }

        return budget

    def validate_content_xp(
        self,
        main_quest_count: int,
        side_quest_count: int,
        dungeon_count: int,
        event_count: int,
        avg_quest_level: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Validate if available content provides enough XP

        Returns:
            {
                "valid": bool,
                "total_xp": int,
                "deficit": int,  # Negative if not enough XP
                "suggestions": List[str]
            }
        """
        requirements = self.calculate_content_requirements()

        # Calculate available XP
        available_xp = (
            main_quest_count * requirements["main_quests"]["avg_xp"]
            + side_quest_count * requirements["side_quests"]["avg_xp"]
            + dungeon_count * requirements["dungeons"]["avg_xp"]
            + event_count * requirements["events"]["avg_xp"]
        )

        deficit = available_xp - self.total_xp_needed
        valid = deficit >= 0

        suggestions = []
        if not valid:
            # Calculate how much more content is needed
            needed_xp = abs(deficit)

            suggestions.append(
                f"Need {needed_xp:,} more XP to reach level {self.max_level}"
            )

            # Suggest content to add
            main_quests_needed = needed_xp // requirements["main_quests"]["avg_xp"]
            if main_quests_needed > 0:
                suggestions.append(f"Add ~{main_quests_needed} main quests")

            side_quests_needed = needed_xp // requirements["side_quests"]["avg_xp"]
            if side_quests_needed > 0:
                suggestions.append(f"Or add ~{side_quests_needed} side quests")

        return {
            "valid": valid,
            "total_xp": available_xp,
            "needed_xp": self.total_xp_needed,
            "deficit": deficit,
            "suggestions": suggestions,
        }

    def scale_quest_xp(self, quest_level: int, base_xp: int = 100) -> int:
        """Scale quest XP based on level"""
        # XP reward scales with level
        return int(base_xp * (1 + (quest_level - 1) * 0.1))

    def distribute_content_across_levels(
        self, content_count: int, min_level: int = 1, max_level: Optional[int] = None
    ) -> List[int]:
        """
        Distribute content across level range

        Returns list of levels for each piece of content.
        """
        if max_level is None:
            max_level = self.max_level

        levels = []
        level_range = max_level - min_level + 1

        # Distribute evenly across levels
        for i in range(content_count):
            # Round-robin distribution
            level = min_level + (i % level_range)
            levels.append(level)

        return sorted(levels)

    def get_stats(self) -> Dict[str, any]:
        """Get leveling system statistics"""
        requirements = self.calculate_content_requirements()

        return {
            "max_level": self.max_level,
            "total_xp_needed": self.total_xp_needed,
            "xp_curve": self.xp_curve.curve_type,
            "content_requirements": requirements,
            "avg_xp_per_level": self.total_xp_needed // self.max_level,
        }
