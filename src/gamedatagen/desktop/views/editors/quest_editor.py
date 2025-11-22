"""Quest Editor"""
from typing import Any, Callable

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen


class QuestEditor:
    def __init__(self, page: ft.Page, config: ProjectConfig, gen: GameDataGen,
                 quest: dict[str, Any], on_save: Callable, on_cancel: Callable) -> None:
        self.page = page
        self.config = config
        self.gen = gen
        self.quest = quest.copy()
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

    async def build(self) -> ft.Column:
        return ft.Column([
            ft.Text(f"Editing: {self.quest.get('name', 'Quest')}", size=24, weight=ft.FontWeight.BOLD),
            ft.TextField(label="Name", value=self.quest.get("name", ""),
                        on_change=lambda e: self.quest.update({"name": e.control.value}), width=400),
            ft.TextField(label="Description", value=self.quest.get("description", ""),
                        multiline=True, min_lines=3,
                        on_change=lambda e: self.quest.update({"description": e.control.value}), width=400),
            ft.TextField(label="Quest Giver ID", value=self.quest.get("quest_giver", ""),
                        on_change=lambda e: self.quest.update({"quest_giver": e.control.value}), width=300),
            ft.TextField(label="Level Requirement", value=str(self.quest.get("level_requirement", 1)),
                        keyboard_type=ft.KeyboardType.NUMBER,
                        on_change=lambda e: self.quest.update({"level_requirement": int(e.control.value or 1)})),
            ft.Dropdown(label="Type", value=self.quest.get("type", "side"),
                       options=[ft.dropdown.Option(t) for t in ["main", "side", "daily", "event"]],
                       on_change=lambda e: self.quest.update({"type": e.control.value})),
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.on_save_callback(self.quest)),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
