"""
Reusable Entity Browser Component
"""

from typing import Any, Callable

import flet as ft


class EntityBrowser:
    """Reusable entity browser with search and filtering"""

    def __init__(
        self,
        page: ft.Page,
        entities: list[dict[str, Any]],
        on_select: Callable[[dict[str, Any]], None],
        on_delete: Callable[[dict[str, Any]], None] | None = None,
        entity_type: str = "entity",
    ) -> None:
        self.page = page
        self.entities = entities
        self.on_select = on_select
        self.on_delete = on_delete
        self.entity_type = entity_type

        # State
        self.search_query = ""
        self.filter_key = None
        self.filter_value = None

        # UI components
        self.search_field: ft.TextField | None = None
        self.list_view: ft.ListView | None = None

    def build(self) -> ft.Column:
        """Build the entity browser"""
        self.search_field = ft.TextField(
            hint_text=f"Search {self.entity_type}...",
            prefix_icon=ft.icons.SEARCH,
            on_change=self.on_search_change,
            width=300,
        )

        self.list_view = ft.ListView(
            spacing=5,
            padding=10,
            expand=True,
        )

        self.refresh_list()

        return ft.Column(
            [
                ft.Row(
                    [
                        self.search_field,
                        ft.Text(
                            f"{len(self.get_filtered_entities())} items",
                            size=12,
                            color=ft.colors.SECONDARY,
                        ),
                    ],
                    spacing=10,
                ),
                self.list_view,
            ],
            spacing=10,
            expand=True,
        )

    def get_filtered_entities(self) -> list[dict[str, Any]]:
        """Get filtered list of entities"""
        filtered = self.entities

        # Apply search
        if self.search_query:
            filtered = [
                e
                for e in filtered
                if self.search_query.lower() in e.get("name", "").lower()
                or self.search_query.lower() in e.get("id", "").lower()
            ]

        # Apply filters
        if self.filter_key and self.filter_value:
            filtered = [e for e in filtered if e.get(self.filter_key) == self.filter_value]

        return filtered

    def refresh_list(self) -> None:
        """Refresh the entity list"""
        self.list_view.controls.clear()

        filtered = self.get_filtered_entities()

        for entity in filtered:
            card = self.create_entity_card(entity)
            self.list_view.controls.append(card)

    async def on_search_change(self, e: ft.ControlEvent) -> None:
        """Handle search input change"""
        self.search_query = e.control.value
        self.refresh_list()
        await self.page.update_async()

    def create_entity_card(self, entity: dict[str, Any]) -> ft.Card:
        """Create an entity card"""
        entity_id = entity.get("id", "unknown")
        entity_name = entity.get("name", "Unknown")
        entity_level = entity.get("level")

        # Build subtitle
        subtitle_parts = [f"ID: {entity_id}"]
        if entity_level:
            subtitle_parts.append(f"Level: {entity_level}")

        # Action buttons
        actions = [
            ft.IconButton(
                icon=ft.icons.EDIT,
                tooltip="Edit",
                on_click=lambda e, ent=entity: self.on_select(ent),
            ),
        ]

        if self.on_delete:
            actions.append(
                ft.IconButton(
                    icon=ft.icons.DELETE,
                    tooltip="Delete",
                    icon_color=ft.colors.ERROR,
                    on_click=lambda e, ent=entity: self.on_delete(ent),
                ),
            )

        return ft.Card(
            content=ft.ListTile(
                leading=ft.Icon(self.get_entity_icon(entity)),
                title=ft.Text(entity_name, weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(" | ".join(subtitle_parts)),
                trailing=ft.Row(actions, spacing=5, tight=True),
                on_click=lambda e, ent=entity: self.on_select(ent),
            ),
        )

    def get_entity_icon(self, entity: dict[str, Any]) -> str:
        """Get icon based on entity type"""
        entity_type = self.entity_type.lower()

        icons = {
            "npc": ft.icons.PERSON,
            "quest": ft.icons.TASK_ALT,
            "item": ft.icons.INVENTORY,
            "enemy": ft.icons.DANGEROUS,
            "zone": ft.icons.MAP,
            "event": ft.icons.EVENT,
        }

        return icons.get(entity_type, ft.icons.DESCRIPTION)

    def set_filter(self, key: str, value: Any) -> None:
        """Set a filter on the entities"""
        self.filter_key = key
        self.filter_value = value
        self.refresh_list()

    def clear_filter(self) -> None:
        """Clear all filters"""
        self.filter_key = None
        self.filter_value = None
        self.search_query = ""
        if self.search_field:
            self.search_field.value = ""
        self.refresh_list()
