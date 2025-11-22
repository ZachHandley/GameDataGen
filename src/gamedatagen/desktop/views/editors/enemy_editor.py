"""Enemy Editor with Loot Tables"""
from typing import Any, Callable

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen
from gamedatagen.desktop.components.loot_table_editor import LootTableEditor


class EnemyEditor:
    def __init__(self, page: ft.Page, config: ProjectConfig, gen: GameDataGen,
                 enemy: dict[str, Any], on_save: Callable, on_cancel: Callable) -> None:
        self.page = page
        self.enemy = enemy.copy()
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel
        self.loot_editor = None

    async def build(self) -> ft.Column:
        loot_table = self.enemy.get("loot_table", [])
        self.loot_editor = LootTableEditor(self.page, loot_table)

        return ft.Column([
            ft.Text(f"Editing: {self.enemy.get('name', 'Enemy')}", size=24, weight=ft.FontWeight.BOLD),
            ft.Tabs(tabs=[
                ft.Tab(text="Basic", icon=ft.icons.INFO, content=ft.Container(content=ft.Column([
                    ft.TextField(label="Name", value=self.enemy.get("name", ""),
                                on_change=lambda e: self.enemy.update({"name": e.control.value}), width=300),
                    ft.TextField(label="Type", value=self.enemy.get("type", ""),
                                on_change=lambda e: self.enemy.update({"type": e.control.value}), width=200),
                    ft.TextField(label="Level", value=str(self.enemy.get("level", 1)),
                                keyboard_type=ft.KeyboardType.NUMBER,
                                on_change=lambda e: self.enemy.update({"level": int(e.control.value or 1)})),
                    ft.TextField(label="HP", value=str(self.enemy.get("hp", 100)),
                                keyboard_type=ft.KeyboardType.NUMBER,
                                on_change=lambda e: self.enemy.update({"hp": int(e.control.value or 100)})),
                ], spacing=15), padding=20)),
                ft.Tab(text="Loot", icon=ft.icons.INVENTORY, content=ft.Container(content=self.loot_editor.build(), padding=20)),
            ]),
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.save_enemy()),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)

    def save_enemy(self) -> None:
        if self.loot_editor:
            self.enemy["loot_table"] = self.loot_editor.get_loot_table()
        self.on_save_callback(self.enemy)
