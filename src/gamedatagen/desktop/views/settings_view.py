"""
Settings View
"""


import flet as ft

from gamedatagen.config import ProjectConfig, save_config
from gamedatagen.core.game_data_gen import GameDataGen


class SettingsView:
    """Settings view"""

    def __init__(
        self, page: ft.Page, config: ProjectConfig, gen: GameDataGen
    ) -> None:
        self.page = page
        self.config = config
        self.gen = gen

        # UI components
        self.status_text: ft.Text | None = None

    async def build(self) -> ft.Column:
        """Build the settings view"""
        self.status_text = ft.Text("", size=14, color=ft.colors.SECONDARY)

        return ft.Column(
            [
                ft.Text("Settings", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                await self.build_api_keys_section(),
                ft.Container(height=20),
                await self.build_generation_settings(),
                ft.Container(height=20),
                await self.build_voice_settings(),
                ft.Container(height=20),
                self.status_text,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    async def build_api_keys_section(self) -> ft.Container:
        """Build API keys section"""
        openai_key_field = ft.TextField(
            label="OpenAI API Key",
            value=self.config.openai_api_key or "",
            password=True,
            can_reveal_password=True,
            on_change=lambda e: setattr(
                self.config, "openai_api_key", e.control.value
            ),
            width=400,
        )

        elevenlabs_key_field = ft.TextField(
            label="ElevenLabs API Key",
            value=self.config.elevenlabs_api_key or "",
            password=True,
            can_reveal_password=True,
            on_change=lambda e: setattr(
                self.config, "elevenlabs_api_key", e.control.value
            ),
            width=400,
        )

        anthropic_key_field = ft.TextField(
            label="Anthropic API Key (optional)",
            value=self.config.anthropic_api_key or "",
            password=True,
            can_reveal_password=True,
            on_change=lambda e: setattr(
                self.config, "anthropic_api_key", e.control.value
            ),
            width=400,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("API Keys", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    openai_key_field,
                    elevenlabs_key_field,
                    anthropic_key_field,
                ],
                spacing=10,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
        )

    async def build_generation_settings(self) -> ft.Container:
        """Build generation settings section"""
        model_dropdown = ft.Dropdown(
            label="Default Model",
            value=self.config.default_model,
            options=[
                ft.dropdown.Option("gpt-4o-mini"),
                ft.dropdown.Option("gpt-4o"),
                ft.dropdown.Option("gpt-4-turbo"),
                ft.dropdown.Option("claude-3-5-sonnet-20241022"),
                ft.dropdown.Option("claude-3-opus-20240229"),
            ],
            on_change=lambda e: setattr(self.config, "default_model", e.control.value),
            width=300,
        )

        temperature_slider = ft.Slider(
            min=0,
            max=1,
            divisions=10,
            label="{value}",
            value=self.config.temperature,
            on_change=lambda e: setattr(self.config, "temperature", e.control.value),
            width=300,
        )

        max_level_field = ft.TextField(
            label="Max Level",
            value=str(self.config.max_level),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: setattr(
                self.config, "max_level", int(e.control.value or 100)
            ),
            width=150,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Content Generation", size=20, weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(height=10),
                    model_dropdown,
                    ft.Column(
                        [
                            ft.Text("Temperature", size=14),
                            temperature_slider,
                        ]
                    ),
                    max_level_field,
                ],
                spacing=10,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
        )

    async def build_voice_settings(self) -> ft.Container:
        """Build voice generation settings"""
        voice_model_dropdown = ft.Dropdown(
            label="Voice Model",
            value=self.config.voice_model,
            options=[
                ft.dropdown.Option("eleven_multilingual_v2", "Multilingual V2"),
                ft.dropdown.Option("eleven_monolingual_v1", "Monolingual V1"),
                ft.dropdown.Option("eleven_turbo_v2", "Turbo V2"),
            ],
            on_change=lambda e: setattr(self.config, "voice_model", e.control.value),
            width=300,
        )

        stability_slider = ft.Slider(
            min=0,
            max=1,
            divisions=10,
            label="{value}",
            value=self.config.voice_stability,
            on_change=lambda e: setattr(
                self.config, "voice_stability", e.control.value
            ),
            width=300,
        )

        similarity_slider = ft.Slider(
            min=0,
            max=1,
            divisions=10,
            label="{value}",
            value=self.config.voice_similarity_boost,
            on_change=lambda e: setattr(
                self.config, "voice_similarity_boost", e.control.value
            ),
            width=300,
        )

        save_button = ft.ElevatedButton(
            "Save Settings",
            icon=ft.icons.SAVE,
            on_click=self.on_save_settings,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Voice Generation", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    voice_model_dropdown,
                    ft.Column(
                        [
                            ft.Text("Stability", size=14),
                            stability_slider,
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Text("Similarity Boost", size=14),
                            similarity_slider,
                        ]
                    ),
                    ft.Container(height=20),
                    save_button,
                ],
                spacing=10,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
        )

    async def on_save_settings(self, e: ft.ControlEvent) -> None:
        """Save settings"""
        try:
            save_config(self.config)
            self.status_text.value = "✓ Settings saved successfully"
            self.status_text.color = ft.colors.GREEN
            await self.page.update_async()
        except Exception as error:
            self.status_text.value = f"Error: {str(error)}"
            self.status_text.color = ft.colors.ERROR
            await self.page.update_async()
