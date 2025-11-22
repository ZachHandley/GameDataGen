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
        self.config = config
        self.gen = gen
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
                ft.Tab(text="Image", icon=ft.icons.IMAGE, content=ft.Container(content=self.build_image_preview(), padding=20)),
            ]),
            ft.Row([
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=lambda e: self.save_enemy()),
                ft.OutlinedButton("Cancel", on_click=lambda e: self.on_cancel_callback()),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)

    def build_image_preview(self) -> ft.Column:
        """Build image preview section"""
        # Check if enemy has an associated image
        enemy_name = self.enemy.get("name", "")
        enemy_type = self.enemy.get("type", "enemy")

        # Look for image file
        image_dir = self.config.images_dir / "enemies"
        possible_names = [
            f"enemy_{enemy_name.lower().replace(' ', '_')}.png",
            f"{enemy_type}_{enemy_name.lower().replace(' ', '_')}.png",
            f"{enemy_name.lower().replace(' ', '_')}.png",
        ]

        image_path = None
        for name in possible_names:
            path = image_dir / name
            if path.exists():
                image_path = path
                break

        if image_path and image_path.exists():
            return ft.Column([
                ft.Text("Enemy Image", size=18, weight=ft.FontWeight.BOLD),
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
                    "No image found for this enemy. Expected locations:\n" +
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
        """Generate enemy image"""
        # Placeholder for image generation
        await self.page.show_snack_bar_async(
            ft.SnackBar(content=ft.Text("Image generation not yet implemented"))
        )

    async def on_regenerate_image(self, e: ft.ControlEvent) -> None:
        """Regenerate enemy image"""
        # Placeholder for image regeneration
        await self.page.show_snack_bar_async(
            ft.SnackBar(content=ft.Text("Image regeneration not yet implemented"))
        )

    def save_enemy(self) -> None:
        if self.loot_editor:
            self.enemy["loot_table"] = self.loot_editor.get_loot_table()
        self.on_save_callback(self.enemy)
