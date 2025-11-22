"""
FastAPI server for GameDataGen

Provides REST API for content generation with local storage.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gamedatagen import __version__
from gamedatagen.config import load_config
from gamedatagen.core.game_data_gen import GameDataGen

# Initialize FastAPI app
app = FastAPI(
    title="GameDataGen API",
    description="AI-powered game content generation API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global GameDataGen instance (initialized on startup)
_gen: Optional[GameDataGen] = None


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize GameDataGen on server startup"""
    global _gen
    try:
        config = load_config()
        _gen = GameDataGen(config)
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Server started but no project configured.")


def get_gen() -> GameDataGen:
    """Get GameDataGen instance"""
    if _gen is None:
        raise HTTPException(
            status_code=500,
            detail="GameDataGen not initialized. Run 'gamedatagen init' first."
        )
    return _gen


# Request/Response models
class GenerateRequest(BaseModel):
    """Request body for generation"""
    count: int = 1
    context: Optional[str] = None
    style: Optional[str] = None
    min_level: Optional[int] = None
    max_level: Optional[int] = None
    zone: Optional[str] = None
    generate_images: bool = False
    quality_check: bool = False


class EntityUpdate(BaseModel):
    """Entity update request"""
    updates: Dict[str, Any]
    regenerate_dependencies: bool = False


# Routes
@app.get("/")
async def root() -> Dict[str, str]:
    """API root"""
    return {
        "name": "GameDataGen API",
        "version": __version__,
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check"""
    return {"status": "healthy"}


@app.post("/generate/{entity_type}")
async def generate_entities(
    entity_type: str,
    request: GenerateRequest,
) -> List[Dict[str, Any]]:
    """
    Generate game content

    Args:
        entity_type: Type of entity to generate (quest, npc, item, etc.)
        request: Generation parameters

    Returns:
        List of generated entities
    """
    gen = get_gen()

    try:
        results = await gen.generate(
            entity_type=entity_type,
            count=request.count,
            context=request.context,
            style=request.style,
            min_level=request.min_level,
            max_level=request.max_level,
            zone=request.zone,
            generate_images=request.generate_images,
            quality_check=request.quality_check,
        )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities/{entity_type}")
async def list_entities(
    entity_type: str,
    zone: Optional[str] = Query(None),
    level_min: Optional[int] = Query(None),
    level_max: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
) -> Dict[str, Any]:
    """
    List entities of a specific type

    Args:
        entity_type: Type of entity
        zone: Filter by zone
        level_min: Minimum level
        level_max: Maximum level
        limit: Max results
        offset: Pagination offset

    Returns:
        Paginated list of entities
    """
    gen = get_gen()

    try:
        entities = gen.list_entities(
            entity_type=entity_type,
            zone=zone,
            level_min=level_min,
            level_max=level_max,
            limit=limit,
            offset=offset,
        )

        return {
            "entity_type": entity_type,
            "count": len(entities),
            "offset": offset,
            "limit": limit,
            "entities": entities,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities/{entity_type}/{entity_id}")
async def get_entity(entity_type: str, entity_id: str) -> Dict[str, Any]:
    """
    Get a specific entity by ID

    Args:
        entity_type: Type of entity
        entity_id: Entity ID

    Returns:
        Entity data
    """
    gen = get_gen()

    try:
        entity = gen.get_entity(entity_type=entity_type, entity_id=entity_id)

        if entity is None:
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found: {entity_type}/{entity_id}"
            )

        return entity

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/entities/{entity_type}/{entity_id}")
async def update_entity(
    entity_type: str,
    entity_id: str,
    request: EntityUpdate,
) -> Dict[str, Any]:
    """
    Update an existing entity

    Args:
        entity_type: Type of entity
        entity_id: Entity ID
        request: Update data

    Returns:
        Updated entity and regeneration results
    """
    gen = get_gen()

    try:
        result = await gen.edit(
            entity_type=entity_type,
            entity_id=entity_id,
            updates=request.updates,
            regenerate_dependencies=request.regenerate_dependencies,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/entities/{entity_type}/{entity_id}")
async def delete_entity(entity_type: str, entity_id: str) -> Dict[str, str]:
    """
    Delete an entity

    Args:
        entity_type: Type of entity
        entity_id: Entity ID

    Returns:
        Success message
    """
    gen = get_gen()

    try:
        gen.delete_entity(entity_type=entity_type, entity_id=entity_id)

        return {"status": "deleted", "entity_id": entity_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge-graph")
async def get_knowledge_graph(
    entity_type: Optional[str] = Query(None),
    predicate: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Query the knowledge graph

    Args:
        entity_type: Filter by entity type
        predicate: Filter by relationship predicate

    Returns:
        Knowledge graph triplets
    """
    gen = get_gen()

    try:
        triplets = gen.query_knowledge_graph(
            entity_type=entity_type,
            predicate=predicate,
        )

        return {
            "count": len(triplets),
            "triplets": [t.dict() for t in triplets],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get project statistics

    Returns:
        Project stats (entity counts, storage, etc.)
    """
    gen = get_gen()

    try:
        return gen.get_stats()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/images/generate")
async def generate_image(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    quality_check: bool = Query(False),
) -> Dict[str, Any]:
    """
    Generate image for an existing entity

    Args:
        entity_type: Type of entity
        entity_id: Entity ID
        quality_check: Enable quality checking

    Returns:
        Generated image info
    """
    gen = get_gen()

    try:
        result = await gen.generate_image(
            entity_type=entity_type,
            entity_id=entity_id,
            quality_check=quality_check,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/{format}")
async def export_content(
    format: str,
    output_dir: Optional[str] = Query(None),
) -> Dict[str, str]:
    """
    Export content to game engine format

    Args:
        format: Export format (unity, unreal, godot, json)
        output_dir: Optional output directory

    Returns:
        Export info
    """
    gen = get_gen()

    if format not in ["unity", "unreal", "godot", "json"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format}"
        )

    try:
        output_path = Path(output_dir) if output_dir else None
        export_path = gen.export(format=format, output_dir=output_path)

        return {
            "format": format,
            "export_path": str(export_path),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Voice generation endpoints
class VoiceGenerationRequest(BaseModel):
    """Voice generation request"""
    voice_id: str
    model: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75


@app.post("/voice/generate/{entity_type}/{entity_id}")
async def generate_voice(
    entity_type: str,
    entity_id: str,
    request: VoiceGenerationRequest,
) -> Dict[str, Any]:
    """
    Generate voice for an entity's dialogue

    Args:
        entity_type: Type of entity
        entity_id: Entity ID
        request: Voice generation parameters

    Returns:
        Generated voice metadata
    """
    gen = get_gen()

    try:
        from gamedatagen.utils.voice_gen import VoiceGenerator

        # Get entity
        entity = gen.get_entity(entity_type=entity_type, entity_id=entity_id)
        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found: {entity_type}/{entity_id}"
            )

        # Check if API key is configured
        config = gen.config
        if not config.elevenlabs_api_key:
            raise HTTPException(
                status_code=500,
                detail="ElevenLabs API key not configured"
            )

        voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)

        # Generate voices
        result = await voice_gen.generate_and_save(
            entity_type=entity_type,
            entity_data=entity,
            output_dir=config.audio_dir / entity_type,
            voice_id=request.voice_id,
            model=request.model,
            stability=request.stability,
            similarity_boost=request.similarity_boost,
        )

        # Update entity
        entity["voice_id"] = request.voice_id
        entity["voice_metadata"] = {
            "audio_files": result["audio_files"],
            "last_generated": result["audio_files"][0]["generated_at"]
            if result["audio_files"]
            else None,
        }

        await gen.edit(
            entity_type=entity_type,
            entity_id=entity_id,
            updates={"voice_id": request.voice_id, "voice_metadata": entity["voice_metadata"]},
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice/regenerate/{entity_type}/{entity_id}")
async def regenerate_voice(
    entity_type: str,
    entity_id: str,
    dialogue_index: Optional[int] = Query(None),
) -> Dict[str, Any]:
    """
    Regenerate voice for entity or specific dialogue line

    Args:
        entity_type: Type of entity
        entity_id: Entity ID
        dialogue_index: Optional specific dialogue index to regenerate

    Returns:
        Regenerated voice metadata
    """
    gen = get_gen()

    try:
        from gamedatagen.utils.voice_gen import VoiceGenerator

        # Get entity
        entity = gen.get_entity(entity_type=entity_type, entity_id=entity_id)
        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found: {entity_type}/{entity_id}"
            )

        voice_id = entity.get("voice_id")
        if not voice_id:
            raise HTTPException(
                status_code=400,
                detail="Entity has no voice_id assigned"
            )

        config = gen.config
        if not config.elevenlabs_api_key:
            raise HTTPException(
                status_code=500,
                detail="ElevenLabs API key not configured"
            )

        voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)

        if dialogue_index is not None:
            # Regenerate specific line
            result = await voice_gen.regenerate_dialogue_line(
                entity_data=entity,
                dialogue_index=dialogue_index,
                output_dir=config.audio_dir / entity_type,
                voice_id=voice_id,
                entity_type=entity_type,
                model=config.voice_model,
                stability=config.voice_stability,
                similarity_boost=config.voice_similarity_boost,
            )

            # Update metadata
            voice_metadata = entity.get("voice_metadata", {})
            audio_files = voice_metadata.get("audio_files", [])

            updated = False
            for af in audio_files:
                if af["dialogue_index"] == dialogue_index:
                    af.update(result)
                    updated = True
                    break

            if not updated:
                audio_files.append(result)

            voice_metadata["audio_files"] = audio_files
            voice_metadata["last_generated"] = result["generated_at"]
            entity["voice_metadata"] = voice_metadata

            return result

        else:
            # Regenerate all dialogue
            result = await voice_gen.generate_and_save(
                entity_type=entity_type,
                entity_data=entity,
                output_dir=config.audio_dir / entity_type,
                voice_id=voice_id,
                model=config.voice_model,
                stability=config.voice_stability,
                similarity_boost=config.voice_similarity_boost,
            )

            entity["voice_metadata"] = {
                "audio_files": result["audio_files"],
                "last_generated": result["audio_files"][0]["generated_at"]
                if result["audio_files"]
                else None,
            }

            # Update entity
            await gen.edit(
                entity_type=entity_type,
                entity_id=entity_id,
                updates={"voice_metadata": entity["voice_metadata"]},
            )

            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/voice/list")
async def list_voices() -> List[Dict[str, Any]]:
    """
    List available ElevenLabs voices

    Returns:
        List of available voices
    """
    gen = get_gen()

    try:
        from gamedatagen.utils.voice_gen import VoiceGenerator

        config = gen.config
        if not config.elevenlabs_api_key:
            raise HTTPException(
                status_code=500,
                detail="ElevenLabs API key not configured"
            )

        voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)
        voices = await voice_gen.list_voices()

        return voices

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice/batch-generate")
async def batch_generate_voices(
    entity_type: str = Query("npc"),
    zone: Optional[str] = Query(None),
    voice_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Batch generate voices for entities without audio

    Args:
        entity_type: Type of entity
        zone: Filter by zone
        voice_id: Assign this voice_id to entities without one

    Returns:
        Batch generation results
    """
    gen = get_gen()

    try:
        from gamedatagen.utils.voice_gen import VoiceGenerator

        config = gen.config
        if not config.elevenlabs_api_key:
            raise HTTPException(
                status_code=500,
                detail="ElevenLabs API key not configured"
            )

        voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)

        # Get entities
        entities = gen.list_entities(entity_type=entity_type, zone=zone)

        # Filter entities needing voice generation
        needs_voice = []
        for entity in entities:
            dialogue = entity.get("dialogue", [])
            voice_metadata = entity.get("voice_metadata", {})
            audio_files = voice_metadata.get("audio_files", [])
            entity_voice_id = entity.get("voice_id") or voice_id

            if not dialogue or not entity_voice_id:
                continue

            if not audio_files or len(audio_files) < len(dialogue):
                needs_voice.append((entity, entity_voice_id))

        # Generate voices
        results = []
        for entity, entity_voice_id in needs_voice:
            entity_id = entity.get("id", "unknown")

            result = await voice_gen.generate_and_save(
                entity_type=entity_type,
                entity_data=entity,
                output_dir=config.audio_dir / entity_type,
                voice_id=entity_voice_id,
                model=config.voice_model,
                stability=config.voice_stability,
                similarity_boost=config.voice_similarity_boost,
            )

            # Update entity
            entity["voice_id"] = entity_voice_id
            entity["voice_metadata"] = {
                "audio_files": result["audio_files"],
                "last_generated": result["audio_files"][0]["generated_at"]
                if result["audio_files"]
                else None,
            }

            await gen.edit(
                entity_type=entity_type,
                entity_id=entity_id,
                updates={"voice_id": entity_voice_id, "voice_metadata": entity["voice_metadata"]},
            )

            results.append({
                "entity_id": entity_id,
                "audio_files": result["audio_files"],
            })

        return {
            "generated_count": len(results),
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
