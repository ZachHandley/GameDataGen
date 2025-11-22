"""
CLI for GameDataGen - AI-powered game content generation
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from gamedatagen import __version__
from gamedatagen.config import init_project, load_config
from gamedatagen.core.game_data_gen import GameDataGen

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="gamedatagen")
def main() -> None:
    """
    🎮 GameDataGen - AI-powered game content generation

    Generate complete game worlds with NPCs, quests, items, enemies, and more.
    """
    pass


@main.command()
@click.argument("project_name")
@click.option("--template", default="mmorpg", help="Project template (mmorpg, roguelike, rpg)")
@click.option("--no-examples", is_flag=True, help="Skip example schemas")
def init(project_name: str, template: str, no_examples: bool) -> None:
    """
    Initialize a new GameDataGen project

    Example:
        gamedatagen init my-rpg-game
    """
    console.print(Panel.fit(
        f"[bold cyan]Initializing project:[/] {project_name}",
        border_style="cyan"
    ))

    project_path = Path.cwd() / project_name

    if project_path.exists():
        console.print(f"[red]✗[/] Directory '{project_name}' already exists")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)

        # Initialize project
        init_project(project_path, template=template, include_examples=not no_examples)

        progress.update(task, description="[green]✓[/] Project created!")

    console.print()
    console.print("[bold green]✓[/] Project initialized successfully!")
    console.print()
    console.print("[bold]Next steps:[/]")
    console.print(f"  1. cd {project_name}")
    console.print("  2. Edit [cyan].gamedatagen/config.yaml[/] with your API keys")
    console.print("  3. gamedatagen generate quests --count 10")
    console.print()
    console.print("[dim]Run 'gamedatagen --help' for more commands[/]")


@main.command()
@click.argument("entity_type")
@click.option("--count", "-n", default=1, help="Number of entities to generate")
@click.option("--context", help="Additional context for generation")
@click.option("--style", help="Generation style (e.g., 'dark-fantasy', 'high-fantasy')")
@click.option("--level-range", help="Level range (e.g., '1-10')")
@click.option("--zone", help="Generate for specific zone")
@click.option("--images", is_flag=True, help="Generate images for entities")
@click.option("--quality-check", is_flag=True, help="Enable image quality control")
def generate(
    entity_type: str,
    count: int,
    context: Optional[str],
    style: Optional[str],
    level_range: Optional[str],
    zone: Optional[str],
    images: bool,
    quality_check: bool,
) -> None:
    """
    Generate game content (quests, npcs, items, enemies, etc.)

    Examples:
        gamedatagen generate quests --count 10
        gamedatagen generate npcs --zone "Shadowmoon Forest" --count 5
        gamedatagen generate items --level-range "50-60" --images
    """
    asyncio.run(_generate(
        entity_type, count, context, style, level_range, zone, images, quality_check
    ))


async def _generate(
    entity_type: str,
    count: int,
    context: Optional[str],
    style: Optional[str],
    level_range: Optional[str],
    zone: Optional[str],
    images: bool,
    quality_check: bool,
) -> None:
    config = load_config()

    console.print(Panel.fit(
        f"[bold cyan]Generating {count} {entity_type}[/]",
        border_style="cyan"
    ))

    gen = GameDataGen(config)

    # Parse level range
    min_level = None
    max_level = None
    if level_range:
        try:
            parts = level_range.split("-")
            min_level = int(parts[0])
            max_level = int(parts[1])
        except (ValueError, IndexError):
            console.print(f"[red]✗[/] Invalid level range: {level_range}")
            sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Generating {entity_type}...", total=count)

        results = await gen.generate(
            entity_type=entity_type,
            count=count,
            context=context,
            style=style,
            min_level=min_level,
            max_level=max_level,
            zone=zone,
            generate_images=images,
            quality_check=quality_check,
        )

        progress.update(task, completed=count)

    console.print()
    console.print(f"[bold green]✓[/] Generated {len(results)} {entity_type}")
    console.print()

    # Show summary table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Type", style="cyan")
    table.add_column("Location", style="yellow")

    for result in results[:10]:  # Show first 10
        table.add_row(
            result.get("id", "")[:12],
            result.get("name", "Unknown"),
            entity_type,
            result.get("filepath", "")
        )

    if len(results) > 10:
        table.add_row("...", f"+ {len(results) - 10} more", "", "")

    console.print(table)
    console.print()
    console.print(f"[dim]Files saved to: assets/game_content/{entity_type}/[/]")


@main.command()
@click.argument("entity_type")
@click.argument("entity_id")
@click.option("--update", help="Updates as JSON string")
@click.option("--regenerate-deps", is_flag=True, help="Regenerate dependent entities")
def edit(
    entity_type: str,
    entity_id: str,
    update: Optional[str],
    regenerate_deps: bool,
) -> None:
    """
    Edit existing game content

    Examples:
        gamedatagen edit quest quest_001 --update '{"difficulty": "hard"}'
        gamedatagen edit npc npc_elder --regenerate-deps
    """
    asyncio.run(_edit(entity_type, entity_id, update, regenerate_deps))


async def _edit(
    entity_type: str,
    entity_id: str,
    update: Optional[str],
    regenerate_deps: bool,
) -> None:
    import json

    config = load_config()
    gen = GameDataGen(config)

    console.print(f"[cyan]Editing {entity_type}:[/] {entity_id}")

    updates = {}
    if update:
        try:
            updates = json.loads(update)
        except json.JSONDecodeError:
            console.print("[red]✗[/] Invalid JSON in --update")
            sys.exit(1)

    result = await gen.edit(
        entity_type=entity_type,
        entity_id=entity_id,
        updates=updates,
        regenerate_dependencies=regenerate_deps,
    )

    console.print(f"[green]✓[/] Updated {entity_type}: {entity_id}")

    if regenerate_deps and result.get("regenerated"):
        console.print(f"  Regenerated {len(result['regenerated'])} dependent entities")


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """
    Start the GameDataGen API server

    The API provides REST endpoints for content generation, stored locally.

    Example:
        gamedatagen serve --port 8000
        curl -X POST "http://localhost:8000/generate/quests?count=5"
    """
    import uvicorn

    console.print(Panel.fit(
        f"[bold cyan]Starting GameDataGen API Server[/]\n"
        f"[dim]http://{host}:{port}[/]",
        border_style="cyan"
    ))

    console.print()
    console.print("[bold]API Endpoints:[/]")
    console.print("  [cyan]POST[/] /generate/{entity_type}")
    console.print("  [cyan]GET[/]  /entities/{entity_type}")
    console.print("  [cyan]GET[/]  /entities/{entity_type}/{entity_id}")
    console.print("  [cyan]PUT[/]  /entities/{entity_type}/{entity_id}")
    console.print("  [cyan]GET[/]  /knowledge-graph")
    console.print()
    console.print(f"[dim]Documentation: http://{host}:{port}/docs[/]")
    console.print()

    uvicorn.run(
        "gamedatagen.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@main.command()
@click.argument(
    "format", type=click.Choice(["bevy", "rust", "bevy-json", "unity", "unreal", "godot", "json"])
)
@click.option("--output", "-o", help="Output directory")
def export(format: str, output: Optional[str]) -> None:
    """
    Export game content for various game engines

    Examples:
        gamedatagen export bevy --output ./bevy-assets  # RON format for Bevy/Rust
        gamedatagen export bevy-json                     # JSON format for Bevy
        gamedatagen export unity --output ./unity-assets
        gamedatagen export json --output ./export
    """
    config = load_config()
    gen = GameDataGen(config)

    output_path = Path(output) if output else Path.cwd() / "exports" / format

    console.print(f"[cyan]Exporting to {format}:[/] {output_path}")

    gen.export(format=format, output_dir=output_path)

    console.print(f"[green]✓[/] Exported to {output_path}")


@main.command()
@click.option("--entity-type", default="npc", help="Entity type to generate voices for")
@click.option("--zone", help="Filter by zone")
@click.option("--voice-id", help="Assign specific voice ID to entities without one")
def generate_voices(entity_type: str, zone: Optional[str], voice_id: Optional[str]) -> None:
    """
    Generate voices for all entities with dialogue but no voice files

    Examples:
        gamedatagen generate-voices
        gamedatagen generate-voices --entity-type npc --zone "Shadowmoon"
        gamedatagen generate-voices --voice-id "21m00Tcm4TlvDq8ikWAM"
    """
    asyncio.run(_generate_voices(entity_type, zone, voice_id))


async def _generate_voices(
    entity_type: str, zone: Optional[str], voice_id: Optional[str]
) -> None:
    config = load_config()

    if not config.elevenlabs_api_key:
        console.print("[red]✗[/] ElevenLabs API key not configured")
        console.print("  Set ELEVENLABS_API_KEY in .gamedatagen/config.yaml")
        sys.exit(1)

    from gamedatagen.utils.voice_gen import VoiceGenerator

    console.print(Panel.fit(
        f"[bold cyan]Generating voices for {entity_type}[/]",
        border_style="cyan"
    ))

    gen = GameDataGen(config)
    voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)

    # Get all entities
    entities = gen.list_entities(entity_type=entity_type, zone=zone)

    # Filter entities needing voice generation
    needs_voice = []
    for entity in entities:
        dialogue = entity.get("dialogue", [])
        voice_metadata = entity.get("voice_metadata", {})
        audio_files = voice_metadata.get("audio_files", [])
        entity_voice_id = entity.get("voice_id") or voice_id

        # Skip if no dialogue
        if not dialogue:
            continue

        # Skip if no voice_id assigned
        if not entity_voice_id:
            console.print(
                f"[yellow]⚠[/] Skipping {entity.get('id')}: no voice_id assigned"
            )
            continue

        # Check if needs generation (no audio files or missing some dialogue)
        if not audio_files or len(audio_files) < len(dialogue):
            needs_voice.append((entity, entity_voice_id))

    if not needs_voice:
        console.print("[green]✓[/] All entities already have voices generated")
        return

    console.print(f"Found {len(needs_voice)} entities needing voice generation")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating voices...", total=len(needs_voice))

        for entity, entity_voice_id in needs_voice:
            entity_id = entity.get("id", "unknown")
            progress.update(task, description=f"Generating voice for {entity_id}...")

            # Generate and save voices
            result = await voice_gen.generate_and_save(
                entity_type=entity_type,
                entity_data=entity,
                output_dir=config.audio_dir / entity_type,
                voice_id=entity_voice_id,
                model=config.voice_model,
                stability=config.voice_stability,
                similarity_boost=config.voice_similarity_boost,
            )

            # Update entity metadata
            entity["voice_id"] = entity_voice_id
            entity["voice_metadata"] = {
                "audio_files": result["audio_files"],
                "last_generated": result["audio_files"][0]["generated_at"]
                if result["audio_files"]
                else None,
            }

            # Save updated entity
            await gen.edit(
                entity_type=entity_type,
                entity_id=entity_id,
                updates={"voice_id": entity_voice_id, "voice_metadata": entity["voice_metadata"]},
            )

            progress.advance(task)

    console.print()
    console.print(f"[bold green]✓[/] Generated voices for {len(needs_voice)} entities")


@main.command()
@click.argument("entity_type")
@click.argument("entity_id")
@click.option("--dialogue-index", type=int, help="Specific dialogue index to regenerate")
@click.option("--all", "regenerate_all", is_flag=True, help="Regenerate all dialogue")
def regenerate_voice(
    entity_type: str,
    entity_id: str,
    dialogue_index: Optional[int],
    regenerate_all: bool,
) -> None:
    """
    Regenerate voice for a specific entity or dialogue line

    Examples:
        gamedatagen regenerate-voice npc npc_elder --dialogue-index 0
        gamedatagen regenerate-voice npc npc_elder --all
    """
    asyncio.run(_regenerate_voice(entity_type, entity_id, dialogue_index, regenerate_all))


async def _regenerate_voice(
    entity_type: str,
    entity_id: str,
    dialogue_index: Optional[int],
    regenerate_all: bool,
) -> None:
    config = load_config()

    if not config.elevenlabs_api_key:
        console.print("[red]✗[/] ElevenLabs API key not configured")
        sys.exit(1)

    from gamedatagen.utils.voice_gen import VoiceGenerator

    gen = GameDataGen(config)
    voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)

    # Get entity
    entity = gen.get_entity(entity_type=entity_type, entity_id=entity_id)
    if not entity:
        console.print(f"[red]✗[/] Entity not found: {entity_type}/{entity_id}")
        sys.exit(1)

    voice_id = entity.get("voice_id")
    if not voice_id:
        console.print("[red]✗[/] Entity has no voice_id assigned")
        sys.exit(1)

    dialogue = entity.get("dialogue", [])
    if not dialogue:
        console.print("[yellow]⚠[/] Entity has no dialogue")
        return

    console.print(f"[cyan]Regenerating voice for {entity_type}:[/] {entity_id}")

    if regenerate_all:
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

        console.print(f"[green]✓[/] Regenerated {len(result['audio_files'])} dialogue lines")

    elif dialogue_index is not None:
        # Regenerate specific dialogue line
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

        # Update or add the audio file entry
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

        console.print(f"[green]✓[/] Regenerated dialogue line {dialogue_index}")

    else:
        console.print("[red]✗[/] Specify --dialogue-index or --all")
        sys.exit(1)

    # Save updated entity
    await gen.edit(
        entity_type=entity_type,
        entity_id=entity_id,
        updates={"voice_metadata": entity["voice_metadata"]},
    )


@main.command()
@click.argument("quest_id")
def regenerate_voices_for_quest(quest_id: str) -> None:
    """
    Regenerate voices for all NPCs in a quest

    Example:
        gamedatagen regenerate-voices-for-quest quest_001
    """
    asyncio.run(_regenerate_voices_for_quest(quest_id))


async def _regenerate_voices_for_quest(quest_id: str) -> None:
    config = load_config()

    if not config.elevenlabs_api_key:
        console.print("[red]✗[/] ElevenLabs API key not configured")
        sys.exit(1)

    from gamedatagen.utils.voice_gen import VoiceGenerator

    gen = GameDataGen(config)
    voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)

    # Get quest
    quest = gen.get_entity(entity_type="quest", entity_id=quest_id)
    if not quest:
        console.print(f"[red]✗[/] Quest not found: {quest_id}")
        sys.exit(1)

    console.print(f"[cyan]Regenerating voices for quest:[/] {quest.get('name', quest_id)}")

    # Find NPCs related to this quest
    quest_giver = quest.get("quest_giver")
    npcs_to_regenerate = []

    if quest_giver:
        npc = gen.get_entity(entity_type="npc", entity_id=quest_giver)
        if npc and npc.get("voice_id"):
            npcs_to_regenerate.append(npc)

    # You might also want to find NPCs mentioned in quest objectives, etc.
    # This is a simplified version

    if not npcs_to_regenerate:
        console.print("[yellow]⚠[/] No NPCs with voice_id found for this quest")
        return

    console.print(f"Found {len(npcs_to_regenerate)} NPCs to regenerate")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Regenerating voices...", total=len(npcs_to_regenerate))

        for npc in npcs_to_regenerate:
            npc_id = npc.get("id", "unknown")
            voice_id = npc.get("voice_id")

            if not voice_id:
                continue

            result = await voice_gen.generate_and_save(
                entity_type="npc",
                entity_data=npc,
                output_dir=config.audio_dir / "npc",
                voice_id=voice_id,
                model=config.voice_model,
                stability=config.voice_stability,
                similarity_boost=config.voice_similarity_boost,
            )

            npc["voice_metadata"] = {
                "audio_files": result["audio_files"],
                "last_generated": result["audio_files"][0]["generated_at"]
                if result["audio_files"]
                else None,
            }

            await gen.edit(
                entity_type="npc",
                entity_id=npc_id,
                updates={"voice_metadata": npc["voice_metadata"]},
            )

            progress.advance(task)

    console.print()
    console.print(f"[bold green]✓[/] Regenerated voices for {len(npcs_to_regenerate)} NPCs")


@main.command()
def list_voices() -> None:
    """
    List available ElevenLabs voices

    Example:
        gamedatagen list-voices
    """
    asyncio.run(_list_voices())


async def _list_voices() -> None:
    config = load_config()

    if not config.elevenlabs_api_key:
        console.print("[red]✗[/] ElevenLabs API key not configured")
        sys.exit(1)

    from gamedatagen.utils.voice_gen import VoiceGenerator

    voice_gen = VoiceGenerator(api_key=config.elevenlabs_api_key)

    console.print(Panel.fit(
        "[bold cyan]Available ElevenLabs Voices[/]",
        border_style="cyan"
    ))
    console.print()

    voices = await voice_gen.list_voices()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Voice ID", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Category", style="cyan")
    table.add_column("Description", style="yellow")

    for voice in voices:
        table.add_row(
            voice["voice_id"][:20] + "...",
            voice["name"],
            voice.get("category", ""),
            (voice.get("description", "")[:50] + "...") if voice.get("description") else "",
        )

    console.print(table)


@main.command()
def desktop() -> None:
    """
    Launch GameDataGen desktop application

    Opens a GUI interface for managing game content, voices, and settings.
    Must be run from a GameDataGen project directory.

    Example:
        gamedatagen desktop
    """
    from gamedatagen.desktop import run_desktop_app

    console.print(Panel.fit(
        "[bold cyan]Launching GameDataGen Desktop[/]",
        border_style="cyan"
    ))

    run_desktop_app()


@main.command()
def status() -> None:
    """
    Show project status and statistics
    """
    config = load_config()
    gen = GameDataGen(config)

    console.print(Panel.fit(
        "[bold cyan]Project Status[/]",
        border_style="cyan"
    ))
    console.print()

    stats = gen.get_stats()

    # Entity counts table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Entity Type", style="cyan")
    table.add_column("Count", justify="right", style="green")

    for entity_type, count in stats["entities"].items():
        table.add_row(entity_type, str(count))

    console.print(table)
    console.print()

    # Knowledge graph stats
    console.print("[bold]Knowledge Graph:[/]")
    console.print(f"  Triplets: {stats['knowledge_graph']['triplets']}")
    console.print(f"  Entities: {stats['knowledge_graph']['entities']}")
    console.print()

    # Storage stats
    console.print("[bold]Storage:[/]")
    console.print(f"  Location: {config.project_root}/assets/game_content")
    console.print(f"  Images: {stats['storage']['images']}")
    console.print(f"  Total size: {stats['storage']['total_size_mb']:.2f} MB")


@main.command()
@click.option("--type", "graph_type", default="all", help="Graph type (relationships, spatial)")
def visualize(graph_type: str) -> None:
    """
    Visualize knowledge graph and relationships
    """
    console.print("[cyan]Generating visualization...[/]")

    config = load_config()
    gen = GameDataGen(config)

    output_file = gen.visualize(graph_type=graph_type)

    console.print(f"[green]✓[/] Visualization saved to: {output_file}")
    console.print("[dim]Open in browser to view[/]")


if __name__ == "__main__":
    main()
