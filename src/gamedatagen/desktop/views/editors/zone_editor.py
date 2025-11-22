"""Zone Editor"""
from typing import Any, Callable
import flet as ft
from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen

class ZoneEditor:
    def __init__(self, page: ft.Page, config: ProjectConfig, gen: GameDataGen,
                 zone: dict[str, Any], on_save: Callable, on_cancel: Callable) -> None:
        self.page = page
        self.zone = zone.copy()
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

    async def build(self) -> ft.Column:
        return ft.Column([
            ft.Text(f"Editing: {self.zone.get('name', 'Zone')}", size=24, weight=ft.FontWeight.BOLD),
            ft.TextField(label="Name", value=self.zone.get("name", ""),
                        on_change=lambda e: self.zone.update({"name": e.control.value}), width=300),
            ft.TextField(label="Description", value=self.zone.get("description", ""),
                        multiline=True, min_lines=3,
                        on_change=lambda e: self.zone.update({"description": e.control.value}), width=400),
            ft.TextField(label="Level Range", value=self.zone.get("level_range", "1-10"),
                        on_change=lambda e: self.zone.update({"level_range": e.control.value}), width=150),
            ft.TextField(label="Biome", value=self.zone.get("biome", ""),
                        on_change=lambda e: self.zone.update({"biome": e.control.value}), width=200),
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.on_save_callback(self.zone)),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
