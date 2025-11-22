"""
Browse and Edit View for All Entity Types
"""

from typing import Any

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen
from gamedatagen.desktop.components.entity_browser import EntityBrowser
from gamedatagen.desktop.views.editors.enemy_editor import EnemyEditor
from gamedatagen.desktop.views.editors.item_editor import ItemEditor
from gamedatagen.desktop.views.editors.npc_editor import NPCEditor
from gamedatagen.desktop.views.editors.quest_editor import QuestEditor
from gamedatagen.desktop.views.editors.zone_editor import ZoneEditor


class BrowseView:
    """Browse and edit all entity types"""

    def __init__(
        self, page: ft.Page, config: ProjectConfig, gen: GameDataGen
    ) -> None:
        self.page = page
        self.config = config
        self.gen = gen

        # State
        self.current_entity_type = "npc"
        self.entities: list[dict[str, Any]] = []
        self.selected_entity: dict[str, Any] | None = None
        self.editor_mode = False

        # UI components
        self.entity_browser: EntityBrowser | None = None
        self.editor_container: ft.Container | None = None
        self.current_editor: Any | None = None

    async def build(self) -> ft.Column:
        """Build the browse view"""
        # Entity type selector
        entity_type_selector = ft.SegmentedButton(
            selected={"npc"},
            allow_multiple_selection=False,
            segments=[
                ft.Segment(
                    value="npc",
                    label=ft.Text("NPCs"),
                    icon=ft.Icon(ft.icons.PERSON),
                ),
                ft.Segment(
                    value="quest",
                    label=ft.Text("Quests"),
                    icon=ft.Icon(ft.icons.TASK_ALT),
                ),
                ft.Segment(
                    value="item",
                    label=ft.Text("Items"),
                    icon=ft.Icon(ft.icons.INVENTORY),
                ),
                ft.Segment(
                    value="enemy",
                    label=ft.Text("Enemies"),
                    icon=ft.Icon(ft.icons.DANGEROUS),
                ),
                ft.Segment(
                    value="zone",
                    label=ft.Text("Zones"),
                    icon=ft.Icon(ft.icons.MAP),
                ),
            ],
            on_change=self.on_entity_type_change,
        )

        # Load initial entities
        await self.load_entities()

        # Create browser
        self.entity_browser = EntityBrowser(
            page=self.page,
            entities=self.entities,
            on_select=self.on_entity_select,
            on_delete=self.on_entity_delete,
            entity_type=self.current_entity_type,
        )

        # Editor container
        self.editor_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.EDIT_NOTE, size=64, color=ft.colors.GREY),
                    ft.Text("Select an entity to edit", size=16, color=ft.colors.SECONDARY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            padding=20,
        )

        return ft.Column(
            [
                ft.Text("Browse & Edit", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                entity_type_selector,
                ft.Container(height=20),
                ft.Row(
                    [
                        ft.Container(
                            content=self.entity_browser.build(),
                            width=350,
                            padding=10,
                            border=ft.border.all(1, ft.colors.OUTLINE),
                            border_radius=10,
                        ),
                        ft.VerticalDivider(width=1),
                        self.editor_container,
                    ],
                    expand=True,
                    spacing=10,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    async def load_entities(self) -> None:
        """Load entities for current type"""
        try:
            self.entities = self.gen.list_entities(entity_type=self.current_entity_type)
        except Exception as error:
            print(f"Error loading {self.current_entity_type}: {error}")
            self.entities = []

    async def on_entity_type_change(self, e: ft.ControlEvent) -> None:
        """Handle entity type change"""
        selected = list(e.control.selected)
        if selected:
            self.current_entity_type = selected[0]
            await self.load_entities()

            # Update browser
            self.entity_browser.entities = self.entities
            self.entity_browser.entity_type = self.current_entity_type
            self.entity_browser.refresh_list()

            # Clear editor
            self.selected_entity = None
            self.editor_mode = False
            self.editor_container.content = ft.Column(
                [
                    ft.Icon(ft.icons.EDIT_NOTE, size=64, color=ft.colors.GREY),
                    ft.Text("Select an entity to edit", size=16, color=ft.colors.SECONDARY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            )

            await self.page.update_async()

    async def on_entity_select(self, entity: dict[str, Any]) -> None:
        """Handle entity selection"""
        self.selected_entity = entity
        self.editor_mode = True

        # Create appropriate editor
        if self.current_entity_type == "npc":
            self.current_editor = NPCEditor(
                self.page, self.config, self.gen, entity, self.on_save, self.on_cancel
            )
        elif self.current_entity_type == "quest":
            self.current_editor = QuestEditor(
                self.page, self.config, self.gen, entity, self.on_save, self.on_cancel
            )
        elif self.current_entity_type == "item":
            self.current_editor = ItemEditor(
                self.page, self.config, self.gen, entity, self.on_save, self.on_cancel
            )
        elif self.current_entity_type == "enemy":
            self.current_editor = EnemyEditor(
                self.page, self.config, self.gen, entity, self.on_save, self.on_cancel
            )
        elif self.current_entity_type == "zone":
            self.current_editor = ZoneEditor(
                self.page, self.config, self.gen, entity, self.on_save, self.on_cancel
            )

        # Build editor
        editor_content = await self.current_editor.build()
        self.editor_container.content = editor_content

        await self.page.update_async()

    async def on_entity_delete(self, entity: dict[str, Any]) -> None:
        """Handle entity deletion"""
        # Show confirmation dialog
        async def confirm_delete():
            try:
                entity_id = entity.get("id")
                self.gen.delete_entity(
                    entity_type=self.current_entity_type, entity_id=entity_id
                )

                # Reload entities
                await self.load_entities()
                self.entity_browser.entities = self.entities
                self.entity_browser.refresh_list()

                # Clear editor if deleted entity was selected
                if self.selected_entity and self.selected_entity.get("id") == entity_id:
                    self.selected_entity = None
                    self.editor_mode = False
                    self.editor_container.content = ft.Column(
                        [
                            ft.Icon(ft.icons.CHECK_CIRCLE, size=64, color=ft.colors.GREEN),
                            ft.Text("Entity deleted", size=16),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )

                await self.close_dialog()
                await self.page.update_async()

            except Exception as error:
                print(f"Error deleting entity: {error}")
                await self.close_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Entity"),
            content=ft.Text(
                f"Are you sure you want to delete '{entity.get('name', 'this entity')}'?\n\n"
                "This action cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.FilledButton(
                    "Delete",
                    icon=ft.icons.DELETE,
                    on_click=lambda e: confirm_delete(),
                ),
            ],
        )

        self.page.dialog = dialog
        dialog.open = True
        await self.page.update_async()

    async def on_save(self, entity: dict[str, Any]) -> None:
        """Handle entity save"""
        try:
            # Update entity
            await self.gen.edit(
                entity_type=self.current_entity_type,
                entity_id=entity.get("id"),
                updates=entity,
            )

            # Reload entities
            await self.load_entities()
            self.entity_browser.entities = self.entities
            self.entity_browser.refresh_list()

            # Show success message
            self.editor_container.content = ft.Column(
                [
                    ft.Icon(ft.icons.CHECK_CIRCLE, size=64, color=ft.colors.GREEN),
                    ft.Text("Changes saved!", size=16),
                    ft.TextButton(
                        "Close", on_click=lambda e: self.on_cancel()
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )

            await self.page.update_async()

        except Exception as error:
            print(f"Error saving entity: {error}")

    async def on_cancel(self) -> None:
        """Handle cancel"""
        self.selected_entity = None
        self.editor_mode = False
        self.editor_container.content = ft.Column(
            [
                ft.Icon(ft.icons.EDIT_NOTE, size=64, color=ft.colors.GREY),
                ft.Text("Select an entity to edit", size=16, color=ft.colors.SECONDARY),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        await self.page.update_async()

    async def close_dialog(self) -> None:
        """Close the current dialog"""
        self.page.dialog.open = False
        await self.page.update_async()
