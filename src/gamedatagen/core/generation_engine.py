"""
Generation Engine with LiteLLM integration

Generates game content using any LLM supported by LiteLLM (100+ models).
"""

import json
from typing import Any, Dict, List, Optional

from litellm import completion
from pydantic import BaseModel

from gamedatagen.core.knowledge_graph import KnowledgeGraph, Triplet
from gamedatagen.core.schema_registry import SchemaRegistry


class GenerationContext(BaseModel):
    """Context for content generation"""

    world_setting: Optional[str] = None
    style: Optional[str] = None
    tone: Optional[str] = None
    existing_entities: Dict[str, List[Dict[str, Any]]] = {}
    custom_context: Optional[str] = None


class GenerationEngine:
    """Content generation engine with LiteLLM"""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.8,
        schema_registry: Optional[SchemaRegistry] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.schema_registry = schema_registry or SchemaRegistry()
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()

    async def generate_entity(
        self,
        entity_type: str,
        context: Optional[GenerationContext] = None,
        specifications: Optional[Dict[str, Any]] = None,
        related_entities: Optional[List[Triplet]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a single entity

        Args:
            entity_type: Type of entity to generate
            context: Generation context (world, style, etc.)
            specifications: Specific requirements (level, zone, etc.)
            related_entities: Related entities from knowledge graph

        Returns:
            Generated entity data
        """
        # Get schema
        schema_def = self.schema_registry.get_schema(entity_type)

        # Build prompt
        prompt = self._build_generation_prompt(
            entity_type=entity_type,
            schema=schema_def.schema,
            context=context or GenerationContext(),
            specifications=specifications or {},
            related_entities=related_entities or [],
        )

        # Call LLM
        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a game content generator. Generate a {entity_type} as valid JSON matching the provided schema. Only return the JSON object, no other text.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )

        # Parse response
        content = response.choices[0].message.content
        entity_data = json.loads(content)

        # Validate against schema
        model = self.schema_registry.get_model(entity_type)
        validated = model(**entity_data)

        return validated.model_dump()

    async def generate_batch(
        self,
        entity_type: str,
        count: int,
        context: Optional[GenerationContext] = None,
        specifications: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple entities

        Args:
            entity_type: Type of entities to generate
            count: Number to generate
            context: Generation context
            specifications: Specific requirements

        Returns:
            List of generated entities
        """
        entities = []

        for i in range(count):
            # Update specifications with index info
            spec = specifications.copy() if specifications else {}
            spec["_index"] = i
            spec["_total"] = count

            # Get related entities from knowledge graph
            # (Could use existing entities for context)
            related = []

            entity = await self.generate_entity(
                entity_type=entity_type,
                context=context,
                specifications=spec,
                related_entities=related,
            )

            entities.append(entity)

        return entities

    def _build_generation_prompt(
        self,
        entity_type: str,
        schema: Dict[str, Any],
        context: GenerationContext,
        specifications: Dict[str, Any],
        related_entities: List[Triplet],
    ) -> str:
        """Build generation prompt"""

        parts = []

        # Entity type and purpose
        parts.append(f"Generate a {entity_type} for an MMORPG game.")

        # World context
        if context.world_setting:
            parts.append(f"\nWorld Setting: {context.world_setting}")

        if context.style:
            parts.append(f"Style: {context.style}")

        if context.tone:
            parts.append(f"Tone: {context.tone}")

        # Specifications
        if specifications:
            parts.append("\nRequirements:")
            for key, value in specifications.items():
                if not key.startswith("_"):  # Skip internal keys
                    parts.append(f"  - {key}: {value}")

        # Related entities (for coherence)
        if related_entities:
            parts.append("\nRelated Entities (maintain coherence):")
            for triplet in related_entities[:5]:  # Limit context
                parts.append(
                    f"  - {triplet.subject.type} '{triplet.subject.id}' "
                    f"{triplet.predicate} {triplet.object.type} '{triplet.object.id}'"
                )

        # Existing entities (for variety)
        if context.existing_entities.get(entity_type):
            existing = context.existing_entities[entity_type][:3]
            parts.append(f"\nExisting {entity_type}s (create something different):")
            for entity in existing:
                name = entity.get("name", entity.get("id", "Unknown"))
                parts.append(f"  - {name}")

        # Custom context
        if context.custom_context:
            parts.append(f"\nAdditional Context: {context.custom_context}")

        # Schema
        parts.append(f"\nJSON Schema to follow:\n{json.dumps(schema, indent=2)}")

        # Final instruction
        parts.append(
            "\nGenerate a creative, thematically appropriate entity that fits this world. "
            "Return ONLY the JSON object matching the schema above."
        )

        return "\n".join(parts)

    async def regenerate_with_edits(
        self,
        entity_type: str,
        original_entity: Dict[str, Any],
        edits: Dict[str, Any],
        context: Optional[GenerationContext] = None,
    ) -> Dict[str, Any]:
        """
        Regenerate entity with specific edits

        Args:
            entity_type: Type of entity
            original_entity: Original entity data
            edits: Fields to update
            context: Generation context

        Returns:
            Updated entity
        """
        # Build prompt for refinement
        schema_def = self.schema_registry.get_schema(entity_type)

        prompt = f"""
Refine this {entity_type} with the following changes:

Original:
{json.dumps(original_entity, indent=2)}

Required Changes:
{json.dumps(edits, indent=2)}

Update the entity to incorporate these changes while maintaining coherence.
Follow this schema:
{json.dumps(schema_def.schema, indent=2)}

Return ONLY the complete updated JSON object.
"""

        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a game content editor. Refine the {entity_type} with requested changes.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature * 0.7,  # Lower temperature for edits
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        entity_data = json.loads(content)

        # Validate
        model = self.schema_registry.get_model(entity_type)
        validated = model(**entity_data)

        return validated.model_dump()

    def set_context_from_entities(
        self, entities: Dict[str, List[Dict[str, Any]]]
    ) -> GenerationContext:
        """Build generation context from existing entities"""

        # Extract world setting from entities if available
        world_setting = None
        style = None

        # Look for world/setting info in entities
        for entity_list in entities.values():
            for entity in entity_list:
                if "world_setting" in entity:
                    world_setting = entity["world_setting"]
                if "style" in entity:
                    style = entity["style"]
                if world_setting and style:
                    break
            if world_setting and style:
                break

        return GenerationContext(
            world_setting=world_setting,
            style=style,
            existing_entities=entities,
        )
