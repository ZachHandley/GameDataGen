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

        # Ensure objectives and rewards exist
        if "objectives" not in self.quest:
            self.quest["objectives"] = []
        if "rewards" not in self.quest:
            self.quest["rewards"] = {"xp": 0, "gold": 0, "items": []}

        # UI components
        self.objectives_list: ft.Column | None = None
        self.reward_items_list: ft.Column | None = None

    async def build(self) -> ft.Column:
        # Build tabs for different sections
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Basic Info", icon=ft.icons.INFO, content=await self.build_basic_info()),
                ft.Tab(text="Objectives", icon=ft.icons.CHECK_CIRCLE, content=await self.build_objectives()),
                ft.Tab(text="Rewards", icon=ft.icons.CARD_GIFTCARD, content=await self.build_rewards()),
                ft.Tab(text="Preview", icon=ft.icons.PREVIEW, content=await self.build_preview()),
            ],
            expand=True,
        )

        return ft.Column([
            ft.Text(f"Editing: {self.quest.get('name', 'Quest')}", size=24, weight=ft.FontWeight.BOLD),
            tabs,
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.on_save_callback(self.quest)),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)

    async def build_basic_info(self) -> ft.Column:
        return ft.Column([
            ft.TextField(label="Name", value=self.quest.get("name", ""),
                        on_change=lambda e: self.quest.update({"name": e.control.value}), width=400),
            ft.TextField(label="Description", value=self.quest.get("description", ""),
                        multiline=True, min_lines=3,
                        on_change=lambda e: self.quest.update({"description": e.control.value}), width=500),
            ft.TextField(label="Quest Giver ID", value=self.quest.get("quest_giver", ""),
                        on_change=lambda e: self.quest.update({"quest_giver": e.control.value}), width=300),
            ft.TextField(label="Zone", value=self.quest.get("zone", ""),
                        on_change=lambda e: self.quest.update({"zone": e.control.value}), width=300),
            ft.TextField(label="Level Requirement", value=str(self.quest.get("level_requirement", 1)),
                        keyboard_type=ft.KeyboardType.NUMBER,
                        on_change=lambda e: self.quest.update({"level_requirement": int(e.control.value or 1)})),
            ft.Dropdown(label="Type", value=self.quest.get("type", "side"),
                       options=[ft.dropdown.Option(t) for t in ["main", "side", "daily", "event"]],
                       on_change=lambda e: self.quest.update({"type": e.control.value})),
        ], scroll=ft.ScrollMode.AUTO, spacing=15)

    async def build_objectives(self) -> ft.Column:
        self.objectives_list = ft.Column([], spacing=10)

        # Build objective cards
        for i, objective in enumerate(self.quest["objectives"]):
            self.objectives_list.controls.append(self.create_objective_card(objective, i))

        return ft.Column([
            ft.Text("Quest Objectives", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Define the steps players must complete", size=12, color=ft.colors.GREY_400),
            self.objectives_list,
            ft.ElevatedButton(
                "Add Objective",
                icon=ft.icons.ADD,
                on_click=self.on_add_objective
            ),
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

    def create_objective_card(self, objective: str, index: int) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.TextField(
                        value=objective,
                        multiline=True,
                        min_lines=1,
                        on_change=lambda e, idx=index: self.on_objective_change(idx, e.control.value),
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        icon_color=ft.colors.RED_400,
                        on_click=lambda e, idx=index: self.on_delete_objective(idx)
                    ),
                ]),
                padding=10,
            )
        )

    async def on_add_objective(self, e: ft.ControlEvent) -> None:
        self.quest["objectives"].append("New objective")
        self.objectives_list.controls.append(
            self.create_objective_card("New objective", len(self.quest["objectives"]) - 1)
        )
        await self.page.update_async()

    def on_objective_change(self, index: int, value: str) -> None:
        self.quest["objectives"][index] = value

    async def on_delete_objective(self, index: int) -> None:
        del self.quest["objectives"][index]
        self.objectives_list.controls.clear()
        for i, objective in enumerate(self.quest["objectives"]):
            self.objectives_list.controls.append(self.create_objective_card(objective, i))
        await self.page.update_async()

    async def build_rewards(self) -> ft.Column:
        rewards = self.quest["rewards"]

        self.reward_items_list = ft.Column([], spacing=10)

        # Build reward item chips
        for item_id in rewards.get("items", []):
            self.reward_items_list.controls.append(
                ft.Chip(
                    label=ft.Text(item_id),
                    on_delete=lambda e, item=item_id: self.on_delete_reward_item(item)
                )
            )

        return ft.Column([
            ft.Text("Quest Rewards", size=18, weight=ft.FontWeight.BOLD),
            ft.TextField(
                label="Experience Points (XP)",
                value=str(rewards.get("xp", 0)),
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e: rewards.update({"xp": int(e.control.value or 0)}),
                width=200,
            ),
            ft.TextField(
                label="Gold",
                value=str(rewards.get("gold", 0)),
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e: rewards.update({"gold": int(e.control.value or 0)}),
                width=200,
            ),
            ft.Text("Reward Items", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.TextField(
                    label="Item ID",
                    hint_text="Enter item ID",
                    width=300,
                    ref=ft.Ref[ft.TextField](),
                    on_submit=self.on_add_reward_item,
                ),
                ft.ElevatedButton(
                    "Add Item",
                    icon=ft.icons.ADD,
                    on_click=self.on_add_reward_item
                ),
            ]),
            ft.Container(
                content=ft.Row(self.reward_items_list.controls, wrap=True, spacing=5),
                padding=10,
            ),
        ], scroll=ft.ScrollMode.AUTO, spacing=15)

    async def on_add_reward_item(self, e: ft.ControlEvent) -> None:
        # Find the text field
        text_field = None
        for control in e.page.controls:
            if isinstance(control, ft.Column):
                # Search recursively for TextField
                text_field = self._find_reward_item_textfield(control)
                if text_field:
                    break

        if text_field and text_field.value:
            item_id = text_field.value.strip()
            if item_id and item_id not in self.quest["rewards"].get("items", []):
                if "items" not in self.quest["rewards"]:
                    self.quest["rewards"]["items"] = []
                self.quest["rewards"]["items"].append(item_id)
                self.reward_items_list.controls.append(
                    ft.Chip(
                        label=ft.Text(item_id),
                        on_delete=lambda e, item=item_id: self.on_delete_reward_item(item)
                    )
                )
                text_field.value = ""
                await self.page.update_async()

    def _find_reward_item_textfield(self, control: ft.Control) -> ft.TextField | None:
        """Recursively find the reward item text field"""
        if isinstance(control, ft.TextField) and control.hint_text == "Enter item ID":
            return control
        if hasattr(control, 'controls'):
            for child in control.controls:
                result = self._find_reward_item_textfield(child)
                if result:
                    return result
        if hasattr(control, 'content'):
            return self._find_reward_item_textfield(control.content)
        return None

    async def on_delete_reward_item(self, item_id: str) -> None:
        if item_id in self.quest["rewards"].get("items", []):
            self.quest["rewards"]["items"].remove(item_id)
            self.reward_items_list.controls.clear()
            for item in self.quest["rewards"]["items"]:
                self.reward_items_list.controls.append(
                    ft.Chip(
                        label=ft.Text(item),
                        on_delete=lambda e, i=item: self.on_delete_reward_item(i)
                    )
                )
            await self.page.update_async()

    async def build_preview(self) -> ft.Column:
        """Build quest preview showing all steps"""
        objectives_preview = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, size=20),
                    ft.Text(f"{i+1}. {obj}", size=14),
                ]),
                padding=5,
            )
            for i, obj in enumerate(self.quest.get("objectives", []))
        ], spacing=5)

        rewards = self.quest.get("rewards", {})
        rewards_text = []
        if rewards.get("xp", 0) > 0:
            rewards_text.append(f"• {rewards['xp']} XP")
        if rewards.get("gold", 0) > 0:
            rewards_text.append(f"• {rewards['gold']} Gold")
        if rewards.get("items"):
            rewards_text.append(f"• Items: {', '.join(rewards['items'])}")

        return ft.Column([
            ft.Text("Quest Preview", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(self.quest.get("name", "Untitled Quest"), size=18, weight=ft.FontWeight.BOLD),
            ft.Text(f"Level {self.quest.get('level_requirement', 1)} • {self.quest.get('type', 'side').title()} Quest",
                   size=12, color=ft.colors.GREY_400),
            ft.Text(self.quest.get("description", "No description"), size=14),
            ft.Divider(),
            ft.Text("Quest Giver", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(self.quest.get("quest_giver", "Unknown"), size=14, color=ft.colors.BLUE_400),
            ft.Text("Zone", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(self.quest.get("zone", "Any"), size=14, color=ft.colors.GREEN_400),
            ft.Divider(),
            ft.Text("Objectives", size=16, weight=ft.FontWeight.BOLD),
            objectives_preview if self.quest.get("objectives") else ft.Text("No objectives defined", italic=True),
            ft.Divider(),
            ft.Text("Rewards", size=16, weight=ft.FontWeight.BOLD),
            ft.Column([ft.Text(text, size=14) for text in rewards_text]) if rewards_text else ft.Text("No rewards", italic=True),
        ], scroll=ft.ScrollMode.AUTO, spacing=10)
