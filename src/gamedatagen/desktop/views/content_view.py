"""
Content Generation View
"""

import asyncio
from typing import Any

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen


class ContentGenerationView:
    """Content generation view"""

    def __init__(
        self, page: ft.Page, config: ProjectConfig, gen: GameDataGen
    ) -> None:
        self.page = page
        self.config = config
        self.gen = gen

        # State
        self.entity_type = "npc"
        self.count = 5
        self.zone = ""
        self.style = ""
        self.level_min = 1
        self.level_max = 10
        self.generate_images = False
        self.generate_voices = False

        # UI components
        self.progress_bar: ft.ProgressBar | None = None
        self.status_text: ft.Text | None = None
        self.results_list: ft.ListView | None = None

    async def build(self) -> ft.Column:
        """Build the content generation view"""
        return ft.Column(
            [
                ft.Text(
                    "Generate Game Content",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                await self.build_generation_form(),
                ft.Divider(),
                await self.build_results_section(),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    async def build_generation_form(self) -> ft.Container:
        """Build generation form"""
        entity_type_dropdown = ft.Dropdown(
            label="Entity Type",
            value="npc",
            options=[
                ft.dropdown.Option("npc", "NPCs"),
                ft.dropdown.Option("quest", "Quests"),
                ft.dropdown.Option("item", "Items"),
                ft.dropdown.Option("enemy", "Enemies"),
                ft.dropdown.Option("zone", "Zones"),
            ],
            on_change=lambda e: setattr(self, "entity_type", e.control.value),
            width=200,
        )

        count_field = ft.TextField(
            label="Count",
            value="5",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: setattr(self, "count", int(e.control.value or 5)),
            width=100,
        )

        zone_field = ft.TextField(
            label="Zone (optional)",
            on_change=lambda e: setattr(self, "zone", e.control.value),
            width=200,
        )

        style_field = ft.TextField(
            label="Style (optional)",
            hint_text="e.g., dark-fantasy",
            on_change=lambda e: setattr(self, "style", e.control.value),
            width=200,
        )

        level_min_field = ft.TextField(
            label="Min Level",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: setattr(self, "level_min", int(e.control.value or 1)),
            width=100,
        )

        level_max_field = ft.TextField(
            label="Max Level",
            value="10",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: setattr(
                self, "level_max", int(e.control.value or 10)
            ),
            width=100,
        )

        images_checkbox = ft.Checkbox(
            label="Generate Images",
            value=False,
            on_change=lambda e: setattr(self, "generate_images", e.control.value),
        )

        voices_checkbox = ft.Checkbox(
            label="Generate Voices (NPCs only)",
            value=False,
            on_change=lambda e: setattr(self, "generate_voices", e.control.value),
        )

        generate_button = ft.ElevatedButton(
            "Generate Content",
            icon=ft.icons.AUTO_AWESOME,
            on_click=self.on_generate_click,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([entity_type_dropdown, count_field]),
                    ft.Row([zone_field, style_field]),
                    ft.Row([level_min_field, level_max_field]),
                    ft.Column([images_checkbox, voices_checkbox]),
                    ft.Container(height=10),
                    generate_button,
                ],
                spacing=10,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
        )

    async def build_results_section(self) -> ft.Container:
        """Build results display section"""
        self.progress_bar = ft.ProgressBar(visible=False, width=400)
        self.status_text = ft.Text("", size=14, color=ft.colors.SECONDARY)
        self.results_list = ft.ListView(
            spacing=10,
            padding=10,
            expand=True,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Results", size=24, weight=ft.FontWeight.BOLD),
                    self.progress_bar,
                    self.status_text,
                    self.results_list,
                ],
                spacing=10,
            ),
            expand=True,
        )

    async def on_generate_click(self, e: ft.ControlEvent) -> None:
        """Handle generate button click"""
        self.progress_bar.visible = True
        self.status_text.value = f"Generating {self.count} {self.entity_type}..."
        self.results_list.controls.clear()
        await self.page.update_async()

        try:
            # Run generation in background task
            await self.page.run_task_async(self.generate_content)
        except Exception as error:
            self.status_text.value = f"Error: {str(error)}"
            self.status_text.color = ft.colors.ERROR
            self.progress_bar.visible = False
            await self.page.update_async()

    async def generate_content(self) -> None:
        """Generate content"""
        try:
            results = await self.gen.generate(
                entity_type=self.entity_type,
                count=self.count,
                context=None,
                style=self.style if self.style else None,
                min_level=self.level_min,
                max_level=self.level_max,
                zone=self.zone if self.zone else None,
                generate_images=self.generate_images,
                quality_check=False,
            )

            # Display results
            for result in results:
                entity_id = result.get("id", "unknown")
                entity_name = result.get("name", "Unknown")

                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE),
                                    title=ft.Text(entity_name),
                                    subtitle=ft.Text(f"ID: {entity_id}"),
                                ),
                            ]
                        ),
                        padding=10,
                    )
                )
                self.results_list.controls.append(card)

            self.status_text.value = (
                f"✓ Generated {len(results)} {self.entity_type} successfully"
            )
            self.status_text.color = ft.colors.GREEN
            self.progress_bar.visible = False
            await self.page.update_async()

        except Exception as error:
            self.status_text.value = f"Error: {str(error)}"
            self.status_text.color = ft.colors.ERROR
            self.progress_bar.visible = False
            await self.page.update_async()
