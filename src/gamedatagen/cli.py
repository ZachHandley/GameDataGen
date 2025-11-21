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
@click.argument("format", type=click.Choice(["unity", "unreal", "godot", "json"]))
@click.option("--output", "-o", help="Output directory")
def export(format: str, output: Optional[str]) -> None:
    """
    Export game content for various game engines

    Examples:
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
