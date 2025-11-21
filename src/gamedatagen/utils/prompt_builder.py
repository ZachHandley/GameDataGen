"""
Prompt Builder for optimized image generation prompts

Model-specific prompt optimization (DALL-E vs Gemini)
"""

from typing import Any, Dict, Optional


class PromptBuilder:
    """Build optimized prompts for different image generation models"""

    def build(
        self,
        model: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        style: Optional[str] = None,
        lighting: Optional[str] = None,
        camera_angle: Optional[str] = None,
        lens_type: Optional[str] = None,
        custom_additions: Optional[str] = None,
        avoid_text_artifacts: bool = True,
    ) -> str:
        """
        Build prompt optimized for specific model

        Args:
            model: Model name (dall-e-3, gemini-imagen-3, etc.)
            entity_type: Type of entity (Item, NPC, Enemy, etc.)
            entity_data: Entity data dict
            style: Art style
            lighting: Lighting description
            camera_angle: Camera angle
            lens_type: Lens type
            custom_additions: Additional prompt text
            avoid_text_artifacts: Explicitly avoid text in image

        Returns:
            Optimized prompt
        """
        if "gemini" in model.lower():
            return self._build_narrative(
                entity_type=entity_type,
                entity_data=entity_data,
                style=style,
                lighting=lighting,
                camera_angle=camera_angle,
                lens_type=lens_type,
                custom_additions=custom_additions,
                avoid_text_artifacts=avoid_text_artifacts,
            )
        else:  # DALL-E 3 and others
            return self._build_structured(
                entity_type=entity_type,
                entity_data=entity_data,
                style=style,
                lighting=lighting,
                camera_angle=camera_angle,
                lens_type=lens_type,
                custom_additions=custom_additions,
                avoid_text_artifacts=avoid_text_artifacts,
            )

    def _build_structured(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        style: Optional[str],
        lighting: Optional[str],
        camera_angle: Optional[str],
        lens_type: Optional[str],
        custom_additions: Optional[str],
        avoid_text_artifacts: bool,
    ) -> str:
        """Build structured prompt (DALL-E 3)"""

        sections = []

        # SUBJECT
        subject = self._build_subject(entity_type, entity_data)
        sections.append(f"SUBJECT: {subject}")

        # STYLE
        if style:
            style_desc = self._get_style_description(style)
            sections.append(f"STYLE: {style_desc}")

        # COMPOSITION
        composition_parts = []
        if camera_angle:
            composition_parts.append(f"{camera_angle} camera angle")
        if lens_type:
            composition_parts.append(f"{lens_type} lens")

        # Add default composition based on entity type
        if "item" in entity_type.lower() or "weapon" in entity_type.lower():
            composition_parts.append("centered on clean background")
        elif "character" in entity_type.lower() or "npc" in entity_type.lower():
            composition_parts.append("portrait composition")
        elif "environment" in entity_type.lower() or "zone" in entity_type.lower():
            composition_parts.append("wide landscape shot")

        if composition_parts:
            sections.append(f"COMPOSITION: {', '.join(composition_parts)}")

        # LIGHTING
        if lighting:
            sections.append(f"LIGHTING: {lighting}")

        # DETAILS
        details = self._build_details(entity_type, entity_data)
        if details:
            sections.append(f"DETAILS: {details}")

        # QUALITY
        quality_parts = ["high quality", "detailed", "professional game art"]
        if avoid_text_artifacts:
            quality_parts.append("no text or writing in the image")

        sections.append(f"QUALITY: {', '.join(quality_parts)}")

        # CUSTOM
        if custom_additions:
            sections.append(f"ADDITIONAL: {custom_additions}")

        return " | ".join(sections)

    def _build_narrative(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        style: Optional[str],
        lighting: Optional[str],
        camera_angle: Optional[str],
        lens_type: Optional[str],
        custom_additions: Optional[str],
        avoid_text_artifacts: bool,
    ) -> str:
        """Build narrative prompt (Gemini Imagen)"""

        parts = []

        # Scene description
        scene = self._build_scene_description(entity_type, entity_data, style)
        parts.append(scene)

        # Camera and technical details
        if camera_angle or lens_type:
            camera_parts = []
            if camera_angle:
                camera_parts.append(f"shot from a {camera_angle}")
            if lens_type:
                camera_parts.append(f"using a {lens_type}")
            parts.append("The image is " + " ".join(camera_parts) + ".")

        # Lighting
        if lighting:
            parts.append(f"The scene is lit with {lighting}.")

        # Quality and restrictions
        quality_desc = "The image should be high quality, detailed, and free of visual artifacts."
        if avoid_text_artifacts:
            quality_desc += " Make sure no text or writing appears in the image."
        parts.append(quality_desc)

        # Custom
        if custom_additions:
            parts.append(custom_additions)

        return " ".join(parts)

    def _build_subject(self, entity_type: str, entity_data: Dict[str, Any]) -> str:
        """Build subject description"""

        type_lower = entity_type.lower()

        if "item" in type_lower or "weapon" in type_lower or "armor" in type_lower:
            return self._build_item_subject(entity_data)
        elif "npc" in type_lower or "character" in type_lower:
            return self._build_character_subject(entity_data)
        elif "enemy" in type_lower or "boss" in type_lower:
            return self._build_enemy_subject(entity_data)
        elif "zone" in type_lower or "environment" in type_lower:
            return self._build_environment_subject(entity_data)
        else:
            name = entity_data.get("name", "game asset")
            desc = entity_data.get("description", "")
            return f"{name}, {desc}" if desc else name

    def _build_item_subject(self, data: Dict[str, Any]) -> str:
        """Build item subject"""
        parts = []

        if data.get("rarity"):
            parts.append(data["rarity"])

        if data.get("name"):
            parts.append(data["name"])

        if data.get("type"):
            parts.append(data["type"])

        if data.get("description"):
            parts.append(data["description"])

        return ", ".join(parts)

    def _build_character_subject(self, data: Dict[str, Any]) -> str:
        """Build character subject"""
        parts = []

        if data.get("name"):
            parts.append(data["name"])

        if data.get("race"):
            parts.append(data["race"])

        if data.get("class"):
            parts.append(data["class"])

        if data.get("appearance"):
            app = data["appearance"]
            if isinstance(app, dict):
                if app.get("clothing"):
                    parts.append(f"wearing {app['clothing']}")
                if app.get("hair_color") or app.get("hairColor"):
                    color = app.get("hair_color") or app.get("hairColor")
                    parts.append(f"{color} hair")

        return ", ".join(parts)

    def _build_enemy_subject(self, data: Dict[str, Any]) -> str:
        """Build enemy subject"""
        parts = []

        if data.get("name"):
            parts.append(data["name"])

        if data.get("type"):
            parts.append(data["type"])

        if data.get("is_boss") or data.get("isBoss"):
            parts.append("boss monster")

        if data.get("description"):
            parts.append(data["description"])

        return ", ".join(parts)

    def _build_environment_subject(self, data: Dict[str, Any]) -> str:
        """Build environment subject"""
        parts = []

        if data.get("name"):
            parts.append(data["name"])

        if data.get("biome"):
            parts.append(f"{data['biome']} biome")

        if data.get("description"):
            parts.append(data["description"])

        return ", ".join(parts)

    def _build_scene_description(
        self, entity_type: str, entity_data: Dict[str, Any], style: Optional[str]
    ) -> str:
        """Build narrative scene description for Gemini"""

        subject = self._build_subject(entity_type, entity_data)

        if style:
            style_desc = self._get_style_description(style)
            return f"A {style_desc} depiction of {subject}."
        else:
            return f"A detailed image of {subject}."

    def _build_details(self, entity_type: str, entity_data: Dict[str, Any]) -> str:
        """Build detail description"""

        details = []

        # Item-specific details
        if entity_data.get("material"):
            details.append(f"made of {entity_data['material']}")

        if entity_data.get("enchantment"):
            details.append(f"glowing with {entity_data['enchantment']} magic")

        # Character details
        if entity_data.get("personality"):
            details.append(entity_data["personality"])

        return ", ".join(details) if details else ""

    def _get_style_description(self, style: str) -> str:
        """Get full style description"""

        style_map = {
            "pixel-art": "pixel art style, retro game graphics, 16-bit aesthetic",
            "fantasy-realistic": "realistic fantasy art, detailed rendering, high fidelity",
            "anime": "anime art style, vibrant colors, manga inspired",
            "painterly": "painterly style, artistic brushstrokes, traditional painting",
            "sketch": "pencil sketch, hand-drawn, monochromatic",
            "comic-book": "comic book art style, bold lines, dynamic composition",
            "low-poly-3d": "low poly 3D art, geometric forms, stylized",
            "isometric": "isometric perspective, game asset, top-down view",
            "oil-painting": "oil painting style, classical art, rich colors",
            "watercolor": "watercolor painting, soft edges, translucent washes",
        }

        return style_map.get(style, style)
