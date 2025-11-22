"""Zone Editor with Loot Pools"""
from typing import Any, Callable

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen
from gamedatagen.desktop.components.loot_table_editor import LootTableEditor


class ZoneEditor:
    def __init__(self, page: ft.Page, config: ProjectConfig, gen: GameDataGen,
                 zone: dict[str, Any], on_save: Callable, on_cancel: Callable) -> None:
        self.page = page
        self.config = config
        self.gen = gen
        self.zone = zone.copy()
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel
        self.loot_pool_editor = None

        # Ensure loot_pool exists
        if "loot_pool" not in self.zone:
            self.zone["loot_pool"] = []

    async def build(self) -> ft.Column:
        loot_pool = self.zone.get("loot_pool", [])
        self.loot_pool_editor = LootTableEditor(self.page, loot_pool)

        return ft.Column([
            ft.Text(f"Editing: {self.zone.get('name', 'Zone')}", size=24, weight=ft.FontWeight.BOLD),
            ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(text="Basic Info", icon=ft.icons.INFO, content=await self.build_basic_info()),
                    ft.Tab(text="Loot Pool", icon=ft.icons.INVENTORY_2, content=self.build_loot_pool()),
                ],
                expand=True,
            ),
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.save_zone()),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)

    async def build_basic_info(self) -> ft.Column:
        return ft.Column([
            ft.TextField(label="Name", value=self.zone.get("name", ""),
                        on_change=lambda e: self.zone.update({"name": e.control.value}), width=300),
            ft.TextField(label="Description", value=self.zone.get("description", ""),
                        multiline=True, min_lines=3,
                        on_change=lambda e: self.zone.update({"description": e.control.value}), width=500),
            ft.TextField(label="Level Range", value=self.zone.get("level_range", "1-10"),
                        on_change=lambda e: self.zone.update({"level_range": e.control.value}), width=150),
            ft.TextField(label="Biome", value=self.zone.get("biome", ""),
                        on_change=lambda e: self.zone.update({"biome": e.control.value}), width=200),
        ], scroll=ft.ScrollMode.AUTO, spacing=15)

    def build_loot_pool(self) -> ft.Column:
        """Build loot pool editor for random items in this zone"""
        return ft.Column([
            ft.Text("Zone Loot Pool", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Define random items that can be found in this zone (chests, containers, world drops, etc.)",
                size=12,
                color=ft.colors.GREY_400
            ),
            ft.Divider(),
            self.loot_pool_editor.build(),
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

    def save_zone(self) -> None:
        """Save zone with loot pool"""
        if self.loot_pool_editor:
            self.zone["loot_pool"] = self.loot_pool_editor.get_loot_table()
        self.on_save_callback(self.zone)
