"""
NPC Editor with Dialogue, Voice, and Image Support
"""

from pathlib import Path
from typing import Any, Callable

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen
from gamedatagen.desktop.components.voice_preview import VoicePreview


class NPCEditor:
    """Comprehensive NPC editor"""

    def __init__(
        self,
        page: ft.Page,
        config: ProjectConfig,
        gen: GameDataGen,
        npc: dict[str, Any],
        on_save: Callable[[dict[str, Any]], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.page = page
        self.config = config
        self.gen = gen
        self.npc = npc.copy()  # Work with a copy
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

        # UI components
        self.dialogue_list: ft.ListView | None = None
        self.voice_preview: VoicePreview | None = None

    async def build(self) -> ft.Column:
        """Build the NPC editor"""
        # Basic fields
        name_field = ft.TextField(
            label="Name",
            value=self.npc.get("name", ""),
            on_change=lambda e: self.npc.update({"name": e.control.value}),
            width=300,
        )

        id_field = ft.TextField(
            label="ID",
            value=self.npc.get("id", ""),
            disabled=True,
            width=300,
        )

        race_field = ft.TextField(
            label="Race",
            value=self.npc.get("race", ""),
            on_change=lambda e: self.npc.update({"race": e.control.value}),
            width=200,
        )

        class_field = ft.TextField(
            label="Class",
            value=self.npc.get("class", ""),
            on_change=lambda e: self.npc.update({"class": e.control.value}),
            width=200,
        )

        level_field = ft.TextField(
            label="Level",
            value=str(self.npc.get("level", 1)),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self.npc.update({"level": int(e.control.value or 1)}),
            width=100,
        )

        personality_field = ft.TextField(
            label="Personality",
            value=self.npc.get("personality", ""),
            on_change=lambda e: self.npc.update({"personality": e.control.value}),
            width=300,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        role_dropdown = ft.Dropdown(
            label="Role",
            value=self.npc.get("role", "merchant"),
            options=[
                ft.dropdown.Option("merchant", "Merchant"),
                ft.dropdown.Option("quest_giver", "Quest Giver"),
                ft.dropdown.Option("trainer", "Trainer"),
                ft.dropdown.Option("guard", "Guard"),
            ],
            on_change=lambda e: self.npc.update({"role": e.control.value}),
            width=200,
        )

        # Voice field
        voice_id_field = ft.TextField(
            label="Voice ID (ElevenLabs)",
            value=self.npc.get("voice_id", ""),
            on_change=lambda e: self.npc.update({"voice_id": e.control.value}),
            width=400,
        )

        # Dialogue editor
        dialogue_section = await self.build_dialogue_editor()

        # Voice preview
        voice_metadata = self.npc.get("voice_metadata", {})
        self.voice_preview = VoicePreview(
            self.page,
            voice_id=self.npc.get("voice_id"),
            audio_files=voice_metadata.get("audio_files", []),
        )

        # Image preview
        image_section = self.build_image_preview()

        # Save/Cancel buttons
        save_button = ft.ElevatedButton(
            "Save Changes",
            icon=ft.icons.SAVE,
            on_click=lambda e: self.on_save_callback(self.npc),
        )

        cancel_button = ft.OutlinedButton(
            "Cancel",
            on_click=lambda e: self.on_cancel_callback(),
        )

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            f"Editing: {self.npc.get('name', 'NPC')}",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.IconButton(
                            icon=ft.icons.CLOSE,
                            on_click=lambda e: self.on_cancel_callback(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Tabs(
                    selected_index=0,
                    tabs=[
                        ft.Tab(
                            text="Basic Info",
                            icon=ft.icons.PERSON,
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        name_field,
                                        id_field,
                                        ft.Row([race_field, class_field, level_field]),
                                        personality_field,
                                        role_dropdown,
                                    ],
                                    spacing=15,
                                ),
                                padding=20,
                            ),
                        ),
                        ft.Tab(
                            text="Dialogue",
                            icon=ft.icons.CHAT,
                            content=ft.Container(content=dialogue_section, padding=20),
                        ),
                        ft.Tab(
                            text="Voice",
                            icon=ft.icons.MIC,
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        voice_id_field,
                                        ft.Divider(),
                                        self.voice_preview.build(),
                                    ],
                                    spacing=15,
                                ),
                                padding=20,
                            ),
                        ),
                        ft.Tab(
                            text="Image",
                            icon=ft.icons.IMAGE,
                            content=ft.Container(content=image_section, padding=20),
                        ),
                    ],
                    expand=True,
                ),
                ft.Container(height=20),
                ft.Row([save_button, cancel_button], spacing=10),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    async def build_dialogue_editor(self) -> ft.Column:
        """Build dialogue editor section"""
        dialogue = self.npc.get("dialogue", [])

        self.dialogue_list = ft.ListView(spacing=10, height=300)

        for i, line in enumerate(dialogue):
            card = self.create_dialogue_card(line, i)
            self.dialogue_list.controls.append(card)

        add_button = ft.ElevatedButton(
            "Add Dialogue Line",
            icon=ft.icons.ADD,
            on_click=self.on_add_dialogue,
        )

        return ft.Column(
            [
                ft.Text("Dialogue Lines", size=18, weight=ft.FontWeight.BOLD),
                self.dialogue_list,
                add_button,
            ],
            spacing=10,
        )

    def create_dialogue_card(self, line: str, index: int) -> ft.Card:
        """Create a dialogue line card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.TextField(
                            value=line,
                            multiline=True,
                            min_lines=1,
                            max_lines=3,
                            expand=True,
                            on_change=lambda e, idx=index: self.on_dialogue_change(
                                idx, e.control.value
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=ft.colors.ERROR,
                            on_click=lambda e, idx=index: self.on_delete_dialogue(idx),
                        ),
                    ]
                ),
                padding=10,
            ),
        )

    async def on_add_dialogue(self, e: ft.ControlEvent) -> None:
        """Add new dialogue line"""
        dialogue = self.npc.get("dialogue", [])
        dialogue.append("New dialogue line")
        self.npc["dialogue"] = dialogue

        # Refresh dialogue list
        self.dialogue_list.controls.append(
            self.create_dialogue_card("New dialogue line", len(dialogue) - 1)
        )
        await self.page.update_async()

    def on_dialogue_change(self, index: int, value: str) -> None:
        """Handle dialogue change"""
        dialogue = self.npc.get("dialogue", [])
        if 0 <= index < len(dialogue):
            dialogue[index] = value

    async def on_delete_dialogue(self, index: int) -> None:
        """Delete dialogue line"""
        dialogue = self.npc.get("dialogue", [])
        if 0 <= index < len(dialogue):
            dialogue.pop(index)
            self.npc["dialogue"] = dialogue

            # Refresh list
            self.dialogue_list.controls.clear()
            for i, line in enumerate(dialogue):
                self.dialogue_list.controls.append(self.create_dialogue_card(line, i))

            await self.page.update_async()

    def build_image_preview(self) -> ft.Column:
        """Build image preview section"""
        # Check if NPC has an associated image
        npc_id = self.npc.get("id", "")
        npc_name = self.npc.get("name", "")

        # Look for image file
        image_dir = self.config.images_dir / "characters"
        possible_names = [
            f"npc_{npc_name.lower().replace(' ', '_')}.png",
            f"character_{npc_name.lower().replace(' ', '_')}.png",
        ]

        image_path = None
        for name in possible_names:
            potential_path = image_dir / name
            if potential_path.exists():
                image_path = potential_path
                break

        if image_path:
            return ft.Column(
                [
                    ft.Text("NPC Image", size=18, weight=ft.FontWeight.BOLD),
                    ft.Image(
                        src=str(image_path),
                        width=300,
                        height=300,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Text(f"File: {image_path.name}", size=12, color=ft.colors.SECONDARY),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Regenerate Image",
                                icon=ft.icons.REFRESH,
                                on_click=self.on_regenerate_image,
                            ),
                        ]
                    ),
                ],
                spacing=10,
            )
        else:
            return ft.Column(
                [
                    ft.Icon(ft.icons.IMAGE_NOT_SUPPORTED, size=64, color=ft.colors.GREY),
                    ft.Text("No image found", color=ft.colors.SECONDARY),
                    ft.ElevatedButton(
                        "Generate Image",
                        icon=ft.icons.AUTO_AWESOME,
                        on_click=self.on_generate_image,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            )

    async def on_generate_image(self, e: ft.ControlEvent) -> None:
        """Generate image for NPC"""
        print("Generate image clicked")
        # TODO: Implement image generation

    async def on_regenerate_image(self, e: ft.ControlEvent) -> None:
        """Regenerate NPC image"""
        print("Regenerate image clicked")
        # TODO: Implement image regeneration
