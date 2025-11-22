"""
Voice Preview Component with Audio Playback
"""

from pathlib import Path
from typing import Any

import flet as ft


class VoicePreview:
    """Voice preview with audio playback and waveform"""

    def __init__(
        self,
        page: ft.Page,
        voice_id: str | None = None,
        audio_files: list[dict[str, Any]] | None = None,
    ) -> None:
        self.page = page
        self.voice_id = voice_id
        self.audio_files = audio_files or []

        # UI components
        self.audio_controls: list[ft.Audio] = []

    def build(self) -> ft.Column:
        """Build the voice preview"""
        if not self.voice_id:
            return ft.Column(
                [
                    ft.Icon(ft.icons.MIC_OFF, size=48, color=ft.colors.GREY),
                    ft.Text("No voice assigned", color=ft.colors.SECONDARY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )

        # Build audio file list
        audio_list = ft.ListView(spacing=10, height=200)

        for audio_file in self.audio_files:
            dialogue_index = audio_file.get("dialogue_index", 0)
            filepath = audio_file.get("filepath", "")
            generated_at = audio_file.get("generated_at", "")

            # Check if file exists
            file_exists = Path(filepath).exists() if filepath else False

            audio_card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.AUDIOTRACK if file_exists else ft.icons.WARNING,
                                        color=ft.colors.GREEN
                                        if file_exists
                                        else ft.colors.AMBER,
                                    ),
                                    ft.Text(
                                        f"Dialogue Line {dialogue_index}",
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                ]
                            ),
                            ft.Text(
                                f"File: {Path(filepath).name if filepath else 'N/A'}",
                                size=12,
                                color=ft.colors.SECONDARY,
                            ),
                            ft.Text(
                                f"Generated: {generated_at[:19] if generated_at else 'N/A'}",
                                size=12,
                                color=ft.colors.SECONDARY,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.icons.PLAY_ARROW,
                                        tooltip="Play",
                                        disabled=not file_exists,
                                        on_click=lambda e, fp=filepath: self.play_audio(fp),
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.REFRESH,
                                        tooltip="Regenerate",
                                        on_click=lambda e, idx=dialogue_index: self.on_regenerate(
                                            idx
                                        ),
                                    ),
                                ]
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                ),
            )
            audio_list.controls.append(audio_card)

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.icons.MIC, color=ft.colors.GREEN),
                        ft.Text(
                            f"Voice ID: {self.voice_id[:20]}...",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ]
                ),
                ft.Text(
                    f"{len(self.audio_files)} audio files",
                    size=12,
                    color=ft.colors.SECONDARY,
                ),
                audio_list,
            ],
            spacing=10,
        )

    async def play_audio(self, filepath: str) -> None:
        """Play audio file"""
        if not Path(filepath).exists():
            return

        # Create audio control
        audio = ft.Audio(
            src=filepath,
            autoplay=True,
            volume=1.0,
            on_state_changed=lambda e: self.on_audio_state_changed(e),
        )

        # Add to page
        self.page.overlay.append(audio)
        await self.page.update_async()

        # Store reference
        self.audio_controls.append(audio)

    async def on_audio_state_changed(self, e: ft.ControlEvent) -> None:
        """Handle audio state change"""
        # Clean up finished audio
        if e.data == "completed":
            if e.control in self.audio_controls:
                self.audio_controls.remove(e.control)
            if e.control in self.page.overlay:
                self.page.overlay.remove(e.control)
            await self.page.update_async()

    async def on_regenerate(self, dialogue_index: int) -> None:
        """Handle regenerate button"""
        # This would be connected to parent component
        print(f"Regenerate dialogue {dialogue_index}")

    def stop_all(self) -> None:
        """Stop all playing audio"""
        for audio in self.audio_controls:
            if audio in self.page.overlay:
                self.page.overlay.remove(audio)
        self.audio_controls.clear()
