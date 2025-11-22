"""
Loot Table Editor Component
"""

from typing import Any

import flet as ft


class LootTableEditor:
    """Editor for loot tables and drop rates"""

    def __init__(self, page: ft.Page, loot_table: list[dict[str, Any]] | None = None) -> None:
        self.page = page
        self.loot_table = loot_table or []

        # UI components
        self.loot_list: ft.ListView | None = None

    def build(self) -> ft.Column:
        """Build the loot table editor"""
        self.loot_list = ft.ListView(
            spacing=10,
            padding=10,
            height=300,
        )

        self.refresh_loot_list()

        add_button = ft.ElevatedButton(
            "Add Loot Item",
            icon=ft.icons.ADD,
            on_click=self.on_add_loot_click,
        )

        return ft.Column(
            [
                ft.Text("Loot Table", size=16, weight=ft.FontWeight.BOLD),
                self.loot_list,
                add_button,
            ],
            spacing=10,
        )

    def refresh_loot_list(self) -> None:
        """Refresh the loot items list"""
        self.loot_list.controls.clear()

        for i, loot_item in enumerate(self.loot_table):
            card = self.create_loot_card(loot_item, i)
            self.loot_list.controls.append(card)

    def create_loot_card(self, loot_item: dict[str, Any], index: int) -> ft.Card:
        """Create a loot item card"""
        item_id = loot_item.get("item_id", "unknown")
        min_quantity = loot_item.get("min_quantity", 1)
        max_quantity = loot_item.get("max_quantity", 1)
        drop_rate = loot_item.get("drop_rate", 1.0)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(f"Item: {item_id}", expand=True),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.ERROR,
                                    on_click=lambda e, idx=index: self.on_delete_loot(idx),
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.TextField(
                                    label="Item ID",
                                    value=item_id,
                                    on_change=lambda e, idx=index: self.on_field_change(
                                        idx, "item_id", e.control.value
                                    ),
                                    width=200,
                                ),
                                ft.TextField(
                                    label="Min Qty",
                                    value=str(min_quantity),
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    on_change=lambda e, idx=index: self.on_field_change(
                                        idx, "min_quantity", int(e.control.value or 1)
                                    ),
                                    width=80,
                                ),
                                ft.TextField(
                                    label="Max Qty",
                                    value=str(max_quantity),
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    on_change=lambda e, idx=index: self.on_field_change(
                                        idx, "max_quantity", int(e.control.value or 1)
                                    ),
                                    width=80,
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text("Drop Rate:", size=14),
                                ft.Slider(
                                    min=0,
                                    max=1,
                                    divisions=100,
                                    label="{value}",
                                    value=drop_rate,
                                    on_change=lambda e, idx=index: self.on_field_change(
                                        idx, "drop_rate", e.control.value
                                    ),
                                    width=200,
                                ),
                                ft.Text(f"{drop_rate:.2%}", size=14),
                            ]
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
        )

    async def on_add_loot_click(self, e: ft.ControlEvent) -> None:
        """Add a new loot item"""
        self.loot_table.append(
            {
                "item_id": "item_",
                "min_quantity": 1,
                "max_quantity": 1,
                "drop_rate": 0.5,
            }
        )
        self.refresh_loot_list()
        await self.page.update_async()

    async def on_delete_loot(self, index: int) -> None:
        """Delete a loot item"""
        if 0 <= index < len(self.loot_table):
            self.loot_table.pop(index)
            self.refresh_loot_list()
            await self.page.update_async()

    def on_field_change(self, index: int, field: str, value: Any) -> None:
        """Handle field change"""
        if 0 <= index < len(self.loot_table):
            self.loot_table[index][field] = value

    def get_loot_table(self) -> list[dict[str, Any]]:
        """Get the current loot table"""
        return self.loot_table
