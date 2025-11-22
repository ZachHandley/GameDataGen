"""
Voice Generation with ElevenLabs TTS
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from pydantic import BaseModel


class GeneratedVoice(BaseModel):
    """Generated voice result"""

    audio_data: bytes
    filepath: str | None = None
    dialogue_index: int | None = None
    generated_at: str


class VoiceGenerationResult(BaseModel):
    """Voice generation result with metadata"""

    voices: list[GeneratedVoice]
    text: str
    voice_id: str
    model: str
    cost: float | None = None


class VoiceGenerator:
    """Voice generation with ElevenLabs"""

    def __init__(self, api_key: str | None = None) -> None:
        self.client = AsyncElevenLabs(api_key=api_key)

    async def generate(
        self,
        text: str,
        voice_id: str,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
    ) -> VoiceGenerationResult:
        """
        Generate voice audio from text

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            model: Model name
            stability: Voice stability (0.0-1.0)
            similarity_boost: Similarity boost (0.0-1.0)
            style: Style exaggeration (0.0-1.0)
            use_speaker_boost: Enable speaker boost

        Returns:
            Generation result with audio data
        """
        voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost,
        )

        # Generate audio
        audio_generator = await self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model,
            voice_settings=voice_settings,
        )

        # Collect audio chunks
        audio_chunks: list[bytes] = []
        async for chunk in audio_generator:
            if isinstance(chunk, bytes):
                audio_chunks.append(chunk)

        audio_data = b"".join(audio_chunks)

        cost = self._estimate_cost(text, model)

        return VoiceGenerationResult(
            voices=[
                GeneratedVoice(
                    audio_data=audio_data,
                    generated_at=datetime.now().isoformat(),
                )
            ],
            text=text,
            voice_id=voice_id,
            model=model,
            cost=cost,
        )

    async def generate_dialogue(
        self,
        dialogue_lines: list[str],
        voice_id: str,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
    ) -> list[VoiceGenerationResult]:
        """
        Generate multiple dialogue lines

        Args:
            dialogue_lines: List of dialogue text
            voice_id: ElevenLabs voice ID
            model: Model name
            stability: Voice stability
            similarity_boost: Similarity boost
            style: Style exaggeration
            use_speaker_boost: Enable speaker boost

        Returns:
            List of generation results
        """
        results: list[VoiceGenerationResult] = []

        for idx, text in enumerate(dialogue_lines):
            result = await self.generate(
                text=text,
                voice_id=voice_id,
                model=model,
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                use_speaker_boost=use_speaker_boost,
            )
            # Add dialogue index to the voice
            result.voices[0].dialogue_index = idx
            results.append(result)

        return results

    async def save_audio(self, audio_data: bytes, filepath: Path) -> None:
        """Save audio data to file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(audio_data)

    async def generate_and_save(
        self,
        entity_type: str,
        entity_data: dict[str, Any],
        output_dir: Path,
        voice_id: str,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> dict[str, Any]:
        """
        Generate and save voice for entity dialogue

        Args:
            entity_type: Type of entity (npc, quest, etc.)
            entity_data: Entity data with dialogue
            output_dir: Output directory for audio files
            voice_id: ElevenLabs voice ID
            model: Model name
            stability: Voice stability
            similarity_boost: Similarity boost

        Returns:
            {
                "audio_files": [{"dialogue_index": int, "filepath": str, "generated_at": str}],
                "voice_id": str,
                "total_cost": float
            }
        """
        # Get dialogue from entity
        dialogue = entity_data.get("dialogue", [])
        if not dialogue:
            return {
                "audio_files": [],
                "voice_id": voice_id,
                "total_cost": 0.0,
            }

        # Generate all dialogue
        results = await self.generate_dialogue(
            dialogue_lines=dialogue,
            voice_id=voice_id,
            model=model,
            stability=stability,
            similarity_boost=similarity_boost,
        )

        # Save files
        entity_id = entity_data.get("id", "entity")
        entity_name = entity_data.get("name", entity_id)
        sanitized = self._sanitize_filename(entity_name)

        audio_files: list[dict[str, Any]] = []
        total_cost = 0.0

        for result in results:
            voice = result.voices[0]
            dialogue_idx = voice.dialogue_index or 0

            filename = f"{entity_type}_{sanitized}_dialogue_{dialogue_idx}.mp3"
            filepath = output_dir / filename

            await self.save_audio(voice.audio_data, filepath)

            audio_files.append(
                {
                    "dialogue_index": dialogue_idx,
                    "filepath": str(filepath),
                    "generated_at": voice.generated_at,
                }
            )

            if result.cost:
                total_cost += result.cost

        return {
            "audio_files": audio_files,
            "voice_id": voice_id,
            "total_cost": total_cost,
        }

    async def regenerate_dialogue_line(
        self,
        entity_data: dict[str, Any],
        dialogue_index: int,
        output_dir: Path,
        voice_id: str,
        entity_type: str = "npc",
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> dict[str, Any]:
        """
        Regenerate a specific dialogue line

        Args:
            entity_data: Entity data
            dialogue_index: Index of dialogue to regenerate
            output_dir: Output directory
            voice_id: ElevenLabs voice ID
            entity_type: Type of entity
            model: Model name
            stability: Voice stability
            similarity_boost: Similarity boost

        Returns:
            {
                "dialogue_index": int,
                "filepath": str,
                "generated_at": str
            }
        """
        dialogue = entity_data.get("dialogue", [])
        if dialogue_index < 0 or dialogue_index >= len(dialogue):
            raise ValueError(f"Invalid dialogue index: {dialogue_index}")

        text = dialogue[dialogue_index]

        result = await self.generate(
            text=text,
            voice_id=voice_id,
            model=model,
            stability=stability,
            similarity_boost=similarity_boost,
        )

        # Save file
        entity_id = entity_data.get("id", "entity")
        entity_name = entity_data.get("name", entity_id)
        sanitized = self._sanitize_filename(entity_name)

        filename = f"{entity_type}_{sanitized}_dialogue_{dialogue_index}.mp3"
        filepath = output_dir / filename

        await self.save_audio(result.voices[0].audio_data, filepath)

        return {
            "dialogue_index": dialogue_index,
            "filepath": str(filepath),
            "generated_at": result.voices[0].generated_at,
        }

    async def list_voices(self) -> list[dict[str, Any]]:
        """
        List available voices from ElevenLabs

        Returns:
            List of voice info dicts
        """
        response = await self.client.voices.get_all()

        voices = []
        for voice in response.voices:
            voices.append(
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": getattr(voice, "description", None),
                    "labels": getattr(voice, "labels", {}),
                }
            )

        return voices

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize entity name for filename"""
        sanitized = name.lower().replace(" ", "_")
        # Remove special chars
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        return sanitized

    def _estimate_cost(self, text: str, model: str) -> float:
        """
        Estimate cost in USD

        ElevenLabs pricing (as of 2024):
        - ~$0.30 per 1000 characters for multilingual models
        - ~$0.18 per 1000 characters for standard models
        """
        char_count = len(text)

        if "multilingual" in model.lower():
            cost_per_1k = 0.30
        else:
            cost_per_1k = 0.18

        return (char_count / 1000) * cost_per_1k
