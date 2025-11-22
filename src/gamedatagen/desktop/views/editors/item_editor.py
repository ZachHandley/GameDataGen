"""Item Editor"""
from typing import Any, Callable
import flet as ft
from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen

class ItemEditor:
    def __init__(self, page: ft.Page, config: ProjectConfig, gen: GameDataGen,
                 item: dict[str, Any], on_save: Callable, on_cancel: Callable) -> None:
        self.page = page
        self.item = item.copy()
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

    async def build(self) -> ft.Column:
        return ft.Column([
            ft.Text(f"Editing: {self.item.get('name', 'Item')}", size=24, weight=ft.FontWeight.BOLD),
            ft.TextField(label="Name", value=self.item.get("name", ""),
                        on_change=lambda e: self.item.update({"name": e.control.value}), width=300),
            ft.Dropdown(label="Type", value=self.item.get("type", "consumable"),
                       options=[ft.dropdown.Option(t) for t in ["weapon", "armor", "consumable", "quest_item"]],
                       on_change=lambda e: self.item.update({"type": e.control.value})),
            ft.Dropdown(label="Rarity", value=self.item.get("rarity", "common"),
                       options=[ft.dropdown.Option(r) for r in ["common", "uncommon", "rare", "epic", "legendary"]],
                       on_change=lambda e: self.item.update({"rarity": e.control.value})),
            ft.TextField(label="Description", value=self.item.get("description", ""),
                        multiline=True, min_lines=2,
                        on_change=lambda e: self.item.update({"description": e.control.value}), width=400),
            ft.TextField(label="Level Requirement", value=str(self.item.get("level_requirement", 1)),
                        keyboard_type=ft.KeyboardType.NUMBER,
                        on_change=lambda e: self.item.update({"level_requirement": int(e.control.value or 1)})),
            ft.TextField(label="Value (Gold)", value=str(self.item.get("value", 0)),
                        keyboard_type=ft.KeyboardType.NUMBER,
                        on_change=lambda e: self.item.update({"value": int(e.control.value or 0)})),
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.on_save_callback(self.item)),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
