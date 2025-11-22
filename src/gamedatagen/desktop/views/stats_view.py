"""
Project Statistics View
"""

from typing import Any

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen


class StatsView:
    """Project statistics view"""

    def __init__(
        self, page: ft.Page, config: ProjectConfig, gen: GameDataGen
    ) -> None:
        self.page = page
        self.config = config
        self.gen = gen

        # State
        self.stats: dict[str, Any] = {}

    async def build(self) -> ft.Column:
        """Build the stats view"""
        # Load stats
        await self.load_stats()

        return ft.Column(
            [
                ft.Text("Project Statistics", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                await self.build_overview_cards(),
                ft.Container(height=20),
                await self.build_entity_breakdown(),
                ft.Container(height=20),
                await self.build_storage_info(),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    async def load_stats(self) -> None:
        """Load project statistics"""
        try:
            self.stats = self.gen.get_stats()
        except Exception as error:
            print(f"Error loading stats: {error}")
            self.stats = {
                "entities": {},
                "knowledge_graph": {"triplets": 0, "entities": 0},
                "storage": {"images": 0, "total_size_mb": 0},
            }

    async def build_overview_cards(self) -> ft.Row:
        """Build overview cards"""
        entities_stats = self.stats.get("entities", {})
        kg_stats = self.stats.get("knowledge_graph", {})
        storage_stats = self.stats.get("storage", {})

        total_entities = sum(entities_stats.values())

        cards = [
            self.create_stat_card(
                "Total Entities",
                str(total_entities),
                ft.icons.DATASET,
                ft.colors.BLUE,
            ),
            self.create_stat_card(
                "Knowledge Graph",
                f"{kg_stats.get('triplets', 0)} triplets",
                ft.icons.DEVICE_HUB,
                ft.colors.GREEN,
            ),
            self.create_stat_card(
                "Storage Used",
                f"{storage_stats.get('total_size_mb', 0):.2f} MB",
                ft.icons.STORAGE,
                ft.colors.ORANGE,
            ),
        ]

        return ft.Row(cards, spacing=20, wrap=True)

    def create_stat_card(
        self, title: str, value: str, icon: str, color: str
    ) -> ft.Card:
        """Create a stat card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, size=40, color=color),
                        ft.Container(height=10),
                        ft.Text(title, size=14, color=ft.colors.SECONDARY),
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                ),
                padding=20,
                width=200,
            ),
        )

    async def build_entity_breakdown(self) -> ft.Container:
        """Build entity type breakdown"""
        entities_stats = self.stats.get("entities", {})

        if not entities_stats:
            return ft.Container(
                content=ft.Text("No entities found", size=16),
                padding=20,
            )

        # Create bar chart data
        chart_data = []
        for entity_type, count in sorted(
            entities_stats.items(), key=lambda x: x[1], reverse=True
        ):
            chart_data.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                entity_type.capitalize(),
                                width=100,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(
                                content=ft.Text(str(count), color=ft.colors.WHITE),
                                bgcolor=ft.colors.BLUE,
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                border_radius=5,
                                width=count * 10 + 50,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=5,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Entity Breakdown", size=20, weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(height=10),
                    ft.Column(chart_data, spacing=5),
                ],
                spacing=10,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
        )

    async def build_storage_info(self) -> ft.Container:
        """Build storage information"""
        storage_stats = self.stats.get("storage", {})

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Storage", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Icon(ft.icons.IMAGE, size=32),
                            ft.Column(
                                [
                                    ft.Text("Images"),
                                    ft.Text(
                                        str(storage_stats.get("images", 0)),
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ]
                            ),
                        ],
                        spacing=20,
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Icon(ft.icons.FOLDER, size=32),
                            ft.Column(
                                [
                                    ft.Text("Project Directory"),
                                    ft.Text(
                                        str(self.config.project_root),
                                        size=12,
                                        color=ft.colors.SECONDARY,
                                    ),
                                ]
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=10,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
        )
