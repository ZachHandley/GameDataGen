"""Desktop application views"""

from gamedatagen.desktop.views.browse_view import BrowseView
from gamedatagen.desktop.views.content_view import ContentGenerationView
from gamedatagen.desktop.views.settings_view import SettingsView
from gamedatagen.desktop.views.stats_view import StatsView
from gamedatagen.desktop.views.voice_view import VoiceManagementView

__all__ = [
    "BrowseView",
    "ContentGenerationView",
    "VoiceManagementView",
    "StatsView",
    "SettingsView",
]
