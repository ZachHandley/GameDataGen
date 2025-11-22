"""
GameDataGen Desktop Application
Built with Flet for cross-platform desktop support
"""

from pathlib import Path

import flet as ft

from gamedatagen.config import load_config
from gamedatagen.core.game_data_gen import GameDataGen
from gamedatagen.desktop.views.browse_view import BrowseView
from gamedatagen.desktop.views.content_view import ContentGenerationView
from gamedatagen.desktop.views.settings_view import SettingsView
from gamedatagen.desktop.views.stats_view import StatsView
from gamedatagen.desktop.views.voice_view import VoiceManagementView


class GameDataGenApp:
    """Main GameDataGen Desktop Application"""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "GameDataGen - AI Game Content Generation"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 900
        self.page.window_min_height = 600

        # State
        self.config = None
        self.game_data_gen = None
        self.current_view = "content"

        # Views
        self.browse_view: BrowseView | None = None
        self.content_view: ContentGenerationView | None = None
        self.voice_view: VoiceManagementView | None = None
        self.stats_view: StatsView | None = None
        self.settings_view: SettingsView | None = None

        # UI Components
        self.view_container: ft.Container | None = None
        self.nav_rail: ft.NavigationRail | None = None

    async def initialize(self) -> None:
        """Initialize the application"""
        try:
            # Load config from current directory
            project_root = Path.cwd()
            self.config = load_config(project_root)
            self.game_data_gen = GameDataGen(self.config)

            # Initialize views
            self.browse_view = BrowseView(
                self.page, self.config, self.game_data_gen
            )
            self.content_view = ContentGenerationView(
                self.page, self.config, self.game_data_gen
            )
            self.voice_view = VoiceManagementView(
                self.page, self.config, self.game_data_gen
            )
            self.stats_view = StatsView(self.page, self.config, self.game_data_gen)
            self.settings_view = SettingsView(
                self.page, self.config, self.game_data_gen
            )

        except FileNotFoundError:
            # No project found - show setup wizard
            await self.show_setup_wizard()

    async def show_setup_wizard(self) -> None:
        """Show setup wizard for new project"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("No GameDataGen Project Found"),
            content=ft.Text(
                "No project found in the current directory.\n\n"
                "Please run 'gamedatagen init <project-name>' first,\n"
                "or open this app from an existing GameDataGen project directory."
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.page.window_close())
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        await self.page.update_async()

    def build_nav_rail(self) -> ft.NavigationRail:
        """Build navigation sidebar"""
        return ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.EDIT_NOTE_OUTLINED,
                    selected_icon=ft.icons.EDIT_NOTE,
                    label="Browse",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.AUTO_AWESOME,
                    selected_icon=ft.icons.AUTO_AWESOME_OUTLINED,
                    label="Generate",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.MIC_OUTLINED,
                    selected_icon=ft.icons.MIC,
                    label="Voices",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ANALYTICS_OUTLINED,
                    selected_icon=ft.icons.ANALYTICS,
                    label="Stats",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                    label="Settings",
                ),
            ],
            on_change=self.on_nav_change,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

    async def on_nav_change(self, e: ft.ControlEvent) -> None:
        """Handle navigation change"""
        index = e.control.selected_index

        if index == 0:
            self.current_view = "browse"
            self.view_container.content = await self.browse_view.build()
        elif index == 1:
            self.current_view = "content"
            self.view_container.content = await self.content_view.build()
        elif index == 2:
            self.current_view = "voice"
            self.view_container.content = await self.voice_view.build()
        elif index == 3:
            self.current_view = "stats"
            self.view_container.content = await self.stats_view.build()
        elif index == 4:
            self.current_view = "settings"
            self.view_container.content = await self.settings_view.build()

        await self.page.update_async()

    async def build(self) -> None:
        """Build the application UI"""
        await self.initialize()

        # If no config, wizard is shown
        if not self.config:
            return

        # Build navigation rail
        self.nav_rail = self.build_nav_rail()

        # Build view container
        self.view_container = ft.Container(
            content=await self.browse_view.build(),
            expand=True,
            padding=20,
        )

        # Build layout
        layout = ft.Row(
            [
                self.nav_rail,
                ft.VerticalDivider(width=1),
                self.view_container,
            ],
            expand=True,
            spacing=0,
        )

        # Add to page
        self.page.add(layout)
        await self.page.update_async()


async def main(page: ft.Page) -> None:
    """Main entry point for Flet app"""
    app = GameDataGenApp(page)
    await app.build()


def run_desktop_app() -> None:
    """Run the desktop application"""
    ft.app(target=main)
