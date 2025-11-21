"""
Image Generation with DALL-E and quality control
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel

from gamedatagen.utils.prompt_builder import PromptBuilder
from gamedatagen.utils.quality_checker import QualityChecker


class GeneratedImage(BaseModel):
    """Generated image result"""

    url: str
    revised_prompt: Optional[str] = None
    filepath: Optional[str] = None


class ImageGenerationResult(BaseModel):
    """Image generation result with metadata"""

    images: List[GeneratedImage]
    prompt: str
    model: str
    cost: Optional[float] = None


class ImageGenerator:
    """Image generation with DALL-E"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.prompt_builder = PromptBuilder()
        self.quality_checker = QualityChecker(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "hd",
        style: str = "vivid",
    ) -> ImageGenerationResult:
        """
        Generate image from prompt

        Args:
            prompt: Image prompt
            model: Model name (dall-e-2, dall-e-3)
            size: Image size
            quality: Image quality (standard, hd)
            style: Style (natural, vivid)

        Returns:
            Generation result
        """
        response = await self.client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,  # type: ignore
            quality=quality if model == "dall-e-3" else None,  # type: ignore
            style=style if model == "dall-e-3" else None,  # type: ignore
            response_format="url",
        )

        if not response.data:
            raise ValueError("No images generated")

        images = [
            GeneratedImage(
                url=img.url,  # type: ignore
                revised_prompt=getattr(img, "revised_prompt", None),
            )
            for img in response.data
        ]

        cost = self._estimate_cost(model, size, quality, len(images))

        return ImageGenerationResult(images=images, prompt=prompt, model=model, cost=cost)

    async def generate_for_entity(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        style: Optional[str] = None,
        custom_additions: Optional[str] = None,
        quality_check: bool = False,
        max_retries: int = 3,
    ) -> ImageGenerationResult:
        """
        Generate image for game entity

        Args:
            entity_type: Type of entity
            entity_data: Entity data
            style: Art style
            custom_additions: Additional prompt text
            quality_check: Enable quality control
            max_retries: Max retry attempts for quality control

        Returns:
            Generation result (best image after QC)
        """
        # Build optimized prompt
        prompt = self.prompt_builder.build(
            model="dall-e-3",
            entity_type=entity_type,
            entity_data=entity_data,
            style=style,
            custom_additions=custom_additions,
            avoid_text_artifacts=True,
        )

        # Get appropriate size for entity type
        size = self._get_size_for_entity(entity_type)

        if quality_check:
            # Generate with quality control
            return await self._generate_with_qc(
                prompt=prompt,
                entity_type=entity_type,
                entity_data=entity_data,
                size=size,
                max_retries=max_retries,
            )
        else:
            # Generate without QC
            return await self.generate(prompt=prompt, size=size, quality="hd", style="vivid")

    async def _generate_with_qc(
        self,
        prompt: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        size: str,
        max_retries: int,
    ) -> ImageGenerationResult:
        """Generate with quality control and auto-retry"""

        best_result = None
        best_score = 0
        attempts = 0

        expected_content = entity_data.get("description") or entity_data.get("name", "game content")

        while attempts < max_retries:
            attempts += 1

            # Generate image
            result = await self.generate(prompt=prompt, size=size, quality="hd", style="vivid")

            # Check quality
            qc_result = await self.quality_checker.check_image(
                image_url=result.images[0].url,
                entity_type=entity_type,
                expected_content=expected_content,
                strict_mode=False,
            )

            # Track best result
            if qc_result.score > best_score:
                best_score = qc_result.score
                best_result = result

            # If passed, use this one
            if qc_result.passed:
                return result

            # If this is the last attempt, return best so far
            if attempts >= max_retries:
                return best_result or result

        return best_result or result  # type: ignore

    async def download_image(self, url: str, filepath: Path) -> None:
        """Download image from URL to file"""

        filepath.parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            filepath.write_bytes(response.content)

    async def generate_and_save(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        output_dir: Path,
        style: Optional[str] = None,
        quality_check: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate and save image for entity

        Returns:
            {
                "filepath": str,
                "url": str,
                "prompt": str,
                "quality_check": QualityCheckResult (if enabled)
            }
        """
        # Generate image
        result = await self.generate_for_entity(
            entity_type=entity_type,
            entity_data=entity_data,
            style=style,
            quality_check=quality_check,
        )

        # Generate filename
        entity_name = entity_data.get("name") or entity_data.get("id", "entity")
        sanitized = entity_name.lower().replace(" ", "_")
        # Remove special chars
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")

        filename = f"{entity_type.lower()}_{sanitized}.png"
        filepath = output_dir / filename

        # Download image
        await self.download_image(result.images[0].url, filepath)

        return {
            "filepath": str(filepath),
            "url": result.images[0].url,
            "prompt": result.prompt,
        }

    def _get_size_for_entity(self, entity_type: str) -> str:
        """Get appropriate image size for entity type"""

        type_lower = entity_type.lower()

        if "environment" in type_lower or "zone" in type_lower or "landscape" in type_lower:
            return "1792x1024"  # Wide landscape

        if "character" in type_lower or "npc" in type_lower or "enemy" in type_lower:
            return "1024x1792"  # Tall portrait

        return "1024x1024"  # Square for items/icons

    def _estimate_cost(self, model: str, size: str, quality: str, n: int) -> float:
        """Estimate cost in USD"""

        if model == "dall-e-3":
            if quality == "hd":
                if size == "1024x1024":
                    return 0.08 * n
                if size in ["1792x1024", "1024x1792"]:
                    return 0.12 * n
            else:  # standard
                if size == "1024x1024":
                    return 0.04 * n
                if size in ["1792x1024", "1024x1792"]:
                    return 0.08 * n

        if model == "dall-e-2":
            if size == "1024x1024":
                return 0.02 * n
            if size == "512x512":
                return 0.018 * n
            if size == "256x256":
                return 0.016 * n

        return 0.04 * n  # Default estimate
