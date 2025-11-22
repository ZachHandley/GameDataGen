"""Item Editor"""
from typing import Any, Callable

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen


class ItemEditor:
    def __init__(self, page: ft.Page, config: ProjectConfig, gen: GameDataGen,
                 item: dict[str, Any], on_save: Callable, on_cancel: Callable) -> None:
        self.page = page
        self.config = config
        self.gen = gen
        self.item = item.copy()
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

    async def build(self) -> ft.Column:
        # Build tabs for different sections
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Basic Info", icon=ft.icons.INFO, content=await self.build_basic_info()),
                ft.Tab(text="Image", icon=ft.icons.IMAGE, content=self.build_image_preview()),
            ],
            expand=True,
        )

        return ft.Column([
            ft.Text(f"Editing: {self.item.get('name', 'Item')}", size=24, weight=ft.FontWeight.BOLD),
            tabs,
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.on_save_callback(self.item)),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)

    async def build_basic_info(self) -> ft.Column:
        return ft.Column([
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
        ], scroll=ft.ScrollMode.AUTO, spacing=15)

    def build_image_preview(self) -> ft.Column:
        """Build image preview section"""
        # Check if item has an associated image
        item_name = self.item.get("name", "")
        item_type = self.item.get("type", "item")

        # Look for image file
        image_dir = self.config.images_dir / "items"
        possible_names = [
            f"item_{item_name.lower().replace(' ', '_')}.png",
            f"{item_type}_{item_name.lower().replace(' ', '_')}.png",
            f"{item_name.lower().replace(' ', '_')}.png",
        ]

        image_path = None
        for name in possible_names:
            path = image_dir / name
            if path.exists():
                image_path = path
                break

        if image_path and image_path.exists():
            return ft.Column([
                ft.Text("Item Image", size=18, weight=ft.FontWeight.BOLD),
                ft.Image(
                    src=str(image_path),
                    width=300,
                    height=300,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(10),
                ),
                ft.Text(f"Path: {image_path.relative_to(self.config.project_root)}", size=12, color=ft.colors.GREY_400),
                ft.ElevatedButton(
                    "Regenerate Image",
                    icon=ft.icons.REFRESH,
                    on_click=self.on_regenerate_image
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=10)
        else:
            return ft.Column([
                ft.Text("No Image Found", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "No image found for this item. Expected locations:\n" +
                    "\n".join(f"• {name}" for name in possible_names),
                    size=12,
                    color=ft.colors.GREY_400,
                ),
                ft.ElevatedButton(
                    "Generate Image",
                    icon=ft.icons.ADD_PHOTO_ALTERNATE,
                    on_click=self.on_generate_image
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=10)

    async def on_generate_image(self, e: ft.ControlEvent) -> None:
        """Generate item image"""
        # Placeholder for image generation
        await self.page.show_snack_bar_async(
            ft.SnackBar(content=ft.Text("Image generation not yet implemented"))
        )

    async def on_regenerate_image(self, e: ft.ControlEvent) -> None:
        """Regenerate item image"""
        # Placeholder for image regeneration
        await self.page.show_snack_bar_async(
            ft.SnackBar(content=ft.Text("Image regeneration not yet implemented"))
        )
