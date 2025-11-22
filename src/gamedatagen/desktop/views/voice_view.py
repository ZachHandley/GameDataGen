"""
Voice Management View
"""

import asyncio
from typing import Any

import flet as ft

from gamedatagen.config import ProjectConfig
from gamedatagen.core.game_data_gen import GameDataGen


class VoiceManagementView:
    """Voice management view"""

    def __init__(
        self, page: ft.Page, config: ProjectConfig, gen: GameDataGen
    ) -> None:
        self.page = page
        self.config = config
        self.gen = gen

        # State
        self.available_voices: list[dict[str, Any]] = []
        self.npcs_list: list[dict[str, Any]] = []
        self.selected_npc: dict[str, Any] | None = None

        # UI components
        self.voices_dropdown: ft.Dropdown | None = None
        self.npcs_list_view: ft.ListView | None = None
        self.npc_details: ft.Container | None = None
        self.status_text: ft.Text | None = None

    async def build(self) -> ft.Column:
        """Build the voice management view"""
        # Check if ElevenLabs API key is configured
        if not self.config.elevenlabs_api_key:
            return ft.Column(
                [
                    ft.Text("Voice Generation", size=32, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.icons.WARNING_AMBER,
                                    size=64,
                                    color=ft.colors.AMBER,
                                ),
                                ft.Text(
                                    "ElevenLabs API Key Not Configured",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "Please configure your ElevenLabs API key in Settings to use voice generation."
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20,
                        ),
                        padding=40,
                        alignment=ft.alignment.center,
                    ),
                ],
                expand=True,
            )

        return ft.Column(
            [
                ft.Text("Voice Management", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row(
                    [
                        await self.build_npcs_panel(),
                        ft.VerticalDivider(width=1),
                        await self.build_voice_assignment_panel(),
                    ],
                    expand=True,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    async def build_npcs_panel(self) -> ft.Container:
        """Build NPCs list panel"""
        # Load NPCs
        await self.load_npcs()

        self.npcs_list_view = ft.ListView(spacing=5, padding=10, expand=True)

        for npc in self.npcs_list:
            npc_id = npc.get("id", "")
            npc_name = npc.get("name", "Unknown")
            voice_id = npc.get("voice_id")
            has_audio = bool(npc.get("voice_metadata", {}).get("audio_files"))

            icon = (
                ft.icons.MIC
                if has_audio
                else ft.icons.MIC_OFF
                if voice_id
                else ft.icons.MIC_NONE
            )
            icon_color = (
                ft.colors.GREEN if has_audio else ft.colors.AMBER if voice_id else None
            )

            card = ft.Card(
                content=ft.ListTile(
                    leading=ft.Icon(icon, color=icon_color),
                    title=ft.Text(npc_name),
                    subtitle=ft.Text(
                        f"Voice: {voice_id[:20]}..." if voice_id else "No voice assigned"
                    ),
                    on_click=lambda e, n=npc: self.on_npc_select(n),
                )
            )
            self.npcs_list_view.controls.append(card)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("NPCs", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"{len(self.npcs_list)} NPCs found",
                        size=12,
                        color=ft.colors.SECONDARY,
                    ),
                    self.npcs_list_view,
                ],
                spacing=10,
            ),
            width=300,
            padding=10,
        )

    async def build_voice_assignment_panel(self) -> ft.Container:
        """Build voice assignment panel"""
        self.status_text = ft.Text("", size=14, color=ft.colors.SECONDARY)

        # Load available voices
        await self.load_available_voices()

        self.voices_dropdown = ft.Dropdown(
            label="Select Voice",
            options=[
                ft.dropdown.Option(v["voice_id"], v["name"])
                for v in self.available_voices
            ],
            width=300,
        )

        assign_button = ft.ElevatedButton(
            "Assign Voice",
            icon=ft.icons.ASSIGNMENT,
            on_click=self.on_assign_voice,
        )

        generate_button = ft.ElevatedButton(
            "Generate All Dialogue",
            icon=ft.icons.AUTO_AWESOME,
            on_click=self.on_generate_all_dialogue,
        )

        batch_generate_button = ft.FilledButton(
            "Batch Generate All NPCs",
            icon=ft.icons.BATCH_PREDICTION,
            on_click=self.on_batch_generate,
        )

        self.npc_details = ft.Container(
            content=ft.Text("Select an NPC to manage voices", size=16),
            padding=20,
            expand=True,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Voice Assignment", size=20, weight=ft.FontWeight.BOLD),
                    self.npc_details,
                    ft.Container(height=20),
                    self.voices_dropdown,
                    ft.Row([assign_button, generate_button], spacing=10),
                    ft.Container(height=20),
                    batch_generate_button,
                    ft.Container(height=10),
                    self.status_text,
                ],
                spacing=10,
            ),
            expand=True,
            padding=10,
        )

    async def load_npcs(self) -> None:
        """Load NPCs from project"""
        try:
            self.npcs_list = self.gen.list_entities(entity_type="npc")
        except Exception as error:
            print(f"Error loading NPCs: {error}")
            self.npcs_list = []

    async def load_available_voices(self) -> None:
        """Load available voices from ElevenLabs"""
        try:
            from gamedatagen.utils.voice_gen import VoiceGenerator

            voice_gen = VoiceGenerator(api_key=self.config.elevenlabs_api_key)
            self.available_voices = await voice_gen.list_voices()
        except Exception as error:
            print(f"Error loading voices: {error}")
            self.available_voices = []

    async def on_npc_select(self, npc: dict[str, Any]) -> None:
        """Handle NPC selection"""
        self.selected_npc = npc

        npc_name = npc.get("name", "Unknown")
        dialogue = npc.get("dialogue", [])
        voice_id = npc.get("voice_id")
        voice_metadata = npc.get("voice_metadata", {})
        audio_files = voice_metadata.get("audio_files", [])

        # Update details panel
        details_content = ft.Column(
            [
                ft.Text(npc_name, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"ID: {npc.get('id', '')}", size=12, color=ft.colors.SECONDARY),
                ft.Container(height=10),
                ft.Text(f"Dialogue Lines: {len(dialogue)}"),
                ft.Text(
                    f"Voice ID: {voice_id if voice_id else 'Not assigned'}",
                    color=ft.colors.GREEN if voice_id else ft.colors.AMBER,
                ),
                ft.Text(
                    f"Generated Audio: {len(audio_files)}/{len(dialogue)} lines",
                    color=ft.colors.GREEN if len(audio_files) == len(dialogue) else None,
                ),
            ],
            spacing=5,
        )

        self.npc_details.content = details_content
        await self.page.update_async()

    async def on_assign_voice(self, e: ft.ControlEvent) -> None:
        """Handle assign voice button"""
        if not self.selected_npc:
            self.status_text.value = "Please select an NPC first"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()
            return

        if not self.voices_dropdown.value:
            self.status_text.value = "Please select a voice"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()
            return

        voice_id = self.voices_dropdown.value
        npc_id = self.selected_npc.get("id")

        try:
            # Update NPC with voice_id
            await self.gen.edit(
                entity_type="npc", entity_id=npc_id, updates={"voice_id": voice_id}
            )

            self.status_text.value = f"✓ Assigned voice to {self.selected_npc.get('name')}"
            self.status_text.color = ft.colors.GREEN
            await self.page.update_async()

            # Reload NPCs
            await self.load_npcs()
            await self.build()

        except Exception as error:
            self.status_text.value = f"Error: {str(error)}"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()

    async def on_generate_all_dialogue(self, e: ft.ControlEvent) -> None:
        """Generate all dialogue for selected NPC"""
        if not self.selected_npc:
            self.status_text.value = "Please select an NPC first"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()
            return

        voice_id = self.selected_npc.get("voice_id")
        if not voice_id:
            self.status_text.value = "NPC has no voice assigned"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()
            return

        self.status_text.value = "Generating voices..."
        self.status_text.color = ft.colors.SECONDARY
        await self.page.update_async()

        try:
            from gamedatagen.utils.voice_gen import VoiceGenerator

            voice_gen = VoiceGenerator(api_key=self.config.elevenlabs_api_key)

            result = await voice_gen.generate_and_save(
                entity_type="npc",
                entity_data=self.selected_npc,
                output_dir=self.config.audio_dir / "npc",
                voice_id=voice_id,
                model=self.config.voice_model,
                stability=self.config.voice_stability,
                similarity_boost=self.config.voice_similarity_boost,
            )

            # Update entity
            await self.gen.edit(
                entity_type="npc",
                entity_id=self.selected_npc.get("id"),
                updates={
                    "voice_metadata": {
                        "audio_files": result["audio_files"],
                        "last_generated": result["audio_files"][0]["generated_at"]
                        if result["audio_files"]
                        else None,
                    }
                },
            )

            self.status_text.value = (
                f"✓ Generated {len(result['audio_files'])} audio files"
            )
            self.status_text.color = ft.colors.GREEN
            await self.page.update_async()

        except Exception as error:
            self.status_text.value = f"Error: {str(error)}"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()

    async def on_batch_generate(self, e: ft.ControlEvent) -> None:
        """Batch generate voices for all NPCs"""
        self.status_text.value = "Batch generating voices..."
        self.status_text.color = ft.colors.SECONDARY
        await self.page.update_async()

        # Show this will take a while
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Batch Voice Generation"),
            content=ft.Text(
                "This will generate voices for all NPCs with dialogue.\n"
                "This may take several minutes depending on how many NPCs you have.\n\n"
                "Continue?"
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.FilledButton(
                    "Continue", on_click=lambda e: self.start_batch_generation()
                ),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        await self.page.update_async()

    async def close_dialog(self) -> None:
        """Close the current dialog"""
        self.page.dialog.open = False
        await self.page.update_async()

    async def start_batch_generation(self) -> None:
        """Start batch generation process"""
        await self.close_dialog()

        try:
            from gamedatagen.utils.voice_gen import VoiceGenerator

            voice_gen = VoiceGenerator(api_key=self.config.elevenlabs_api_key)

            generated = 0
            for npc in self.npcs_list:
                voice_id = npc.get("voice_id")
                dialogue = npc.get("dialogue", [])
                voice_metadata = npc.get("voice_metadata", {})
                audio_files = voice_metadata.get("audio_files", [])

                if not voice_id or not dialogue:
                    continue

                if len(audio_files) >= len(dialogue):
                    continue

                # Generate
                result = await voice_gen.generate_and_save(
                    entity_type="npc",
                    entity_data=npc,
                    output_dir=self.config.audio_dir / "npc",
                    voice_id=voice_id,
                    model=self.config.voice_model,
                    stability=self.config.voice_stability,
                    similarity_boost=self.config.voice_similarity_boost,
                )

                # Update
                await self.gen.edit(
                    entity_type="npc",
                    entity_id=npc.get("id"),
                    updates={
                        "voice_metadata": {
                            "audio_files": result["audio_files"],
                            "last_generated": result["audio_files"][0]["generated_at"]
                            if result["audio_files"]
                            else None,
                        }
                    },
                )

                generated += 1

            self.status_text.value = f"✓ Generated voices for {generated} NPCs"
            self.status_text.color = ft.colors.GREEN
            await self.page.update_async()

        except Exception as error:
            self.status_text.value = f"Error: {str(error)}"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()
