"""
Theme Manager for MailMind UI

Implements Story 2.3 AC1: CustomTkinter Framework with Dark/Light Theme
- Dark/light theme toggle with system preference detection
- Custom MailMind color scheme
- Theme persistence in database (user_preferences table)
- Dynamic theme switching without restart

Usage:
    theme_mgr = ThemeManager(db_manager=db)
    theme_mgr.set_theme("dark")  # or "light"
    current_theme = theme_mgr.get_current_theme()
"""

import logging
import platform
from typing import Literal, Dict, Any, Optional
import customtkinter as ctk

logger = logging.getLogger(__name__)

ThemeMode = Literal["dark", "light"]


class ThemeManager:
    """
    Manages application theme (dark/light mode) with database persistence.

    Features:
    - System theme preference detection (Windows/macOS/Linux)
    - Theme persistence in database
    - Dynamic theme switching
    - Custom MailMind color scheme
    """

    # MailMind Brand Colors (from Story 2.3 spec)
    COLORS = {
        "dark": {
            "bg": "#1a1a1a",           # Main background
            "fg": "#e0e0e0",           # Text color
            "accent": "#4a9eff",       # Primary accent (blue)
            "hover": "#2a2a2a",        # Hover state
            "selected": "#3a3a3a",     # Selected state
        },
        "light": {
            "bg": "#ffffff",           # Main background
            "fg": "#1a1a1a",           # Text color
            "accent": "#2563eb",       # Primary accent (darker blue)
            "hover": "#f5f5f5",        # Hover state
            "selected": "#e5e5e5",     # Selected state
        },
        # Priority colors (same in both themes)
        "priority": {
            "high": "#ef4444",         # Red
            "medium": "#f59e0b",       # Orange
            "low": "#3b82f6",          # Blue
        }
    }

    def __init__(self, db_manager=None):
        """
        Initialize ThemeManager.

        Args:
            db_manager: Optional DatabaseManager instance for theme persistence.
                       If None, theme changes won't be persisted.
        """
        self.db_manager = db_manager
        self._current_theme: ThemeMode = "dark"
        self._observers = []  # List of callbacks to notify on theme change

        # Load saved theme or detect system preference
        self._load_theme()

        logger.info(f"ThemeManager initialized with theme: {self._current_theme}")

    def _load_theme(self):
        """Load theme from database or detect system preference."""
        try:
            # Try to load from database first
            if self.db_manager:
                prefs = self.db_manager.get_preference("ui_theme")
                if prefs and prefs in ["dark", "light"]:
                    self._current_theme = prefs
                    logger.debug(f"Loaded theme from database: {self._current_theme}")
                    return
        except Exception as e:
            logger.warning(f"Failed to load theme from database: {e}")

        # Fall back to system preference
        system_theme = self._detect_system_theme()
        self._current_theme = system_theme
        logger.debug(f"Using system theme: {self._current_theme}")

    def _detect_system_theme(self) -> ThemeMode:
        """
        Detect system theme preference (Windows/macOS/Linux).

        Returns:
            "dark" or "light" based on system settings
        """
        try:
            # CustomTkinter includes darkdetect which handles cross-platform detection
            import darkdetect

            is_dark = darkdetect.isDark()
            if is_dark is None:
                # Can't detect, default to dark
                logger.debug("Cannot detect system theme, defaulting to dark")
                return "dark"

            theme = "dark" if is_dark else "light"
            logger.debug(f"Detected system theme: {theme}")
            return theme

        except Exception as e:
            logger.warning(f"Failed to detect system theme: {e}, defaulting to dark")
            return "dark"

    def get_current_theme(self) -> ThemeMode:
        """
        Get current theme mode.

        Returns:
            Current theme: "dark" or "light"
        """
        return self._current_theme

    def set_theme(self, mode: ThemeMode):
        """
        Set theme mode and apply changes.

        Args:
            mode: Theme mode ("dark" or "light")
        """
        if mode not in ["dark", "light"]:
            raise ValueError(f"Invalid theme mode: {mode}. Must be 'dark' or 'light'")

        if mode == self._current_theme:
            logger.debug(f"Theme already set to {mode}, skipping")
            return

        old_theme = self._current_theme
        self._current_theme = mode

        # Apply theme to CustomTkinter
        ctk.set_appearance_mode(mode)

        # Persist to database
        self._save_theme()

        # Notify observers (UI components)
        self._notify_observers(old_theme, mode)

        logger.info(f"Theme changed: {old_theme} → {mode}")

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.set_theme(new_theme)

    def _save_theme(self):
        """Persist theme choice to database."""
        try:
            if self.db_manager:
                self.db_manager.set_preference("ui_theme", self._current_theme)
                logger.debug(f"Theme persisted to database: {self._current_theme}")
        except Exception as e:
            logger.error(f"Failed to save theme to database: {e}")

    def add_observer(self, callback):
        """
        Register callback to be notified on theme changes.

        Args:
            callback: Function with signature (old_theme, new_theme) -> None
        """
        if callback not in self._observers:
            self._observers.append(callback)
            callback_name = getattr(callback, '__name__', repr(callback))
            logger.debug(f"Added theme observer: {callback_name}")

    def remove_observer(self, callback):
        """Unregister theme change callback."""
        if callback in self._observers:
            self._observers.remove(callback)
            callback_name = getattr(callback, '__name__', repr(callback))
            logger.debug(f"Removed theme observer: {callback_name}")

    def _notify_observers(self, old_theme: ThemeMode, new_theme: ThemeMode):
        """Notify all observers of theme change."""
        for callback in self._observers:
            try:
                callback(old_theme, new_theme)
            except Exception as e:
                callback_name = getattr(callback, '__name__', repr(callback))
                logger.error(f"Theme observer {callback_name} failed: {e}")

    def get_color(self, category: str, key: str) -> str:
        """
        Get color value for current theme.

        Args:
            category: Color category ("dark", "light", or "priority")
            key: Color key (e.g., "bg", "fg", "accent", "high")

        Returns:
            Hex color string (e.g., "#1a1a1a")
        """
        if category == "priority":
            return self.COLORS["priority"][key]

        theme_colors = self.COLORS.get(self._current_theme, self.COLORS["dark"])
        return theme_colors.get(key, "#000000")

    def get_theme_colors(self) -> Dict[str, str]:
        """
        Get all colors for current theme.

        Returns:
            Dictionary of color keys to hex values
        """
        return self.COLORS[self._current_theme].copy()

    def get_priority_color(self, priority: str) -> str:
        """
        Get color for priority level.

        Args:
            priority: Priority level ("high", "medium", "low")

        Returns:
            Hex color string
        """
        priority_lower = priority.lower()
        return self.COLORS["priority"].get(priority_lower, self.COLORS["priority"]["medium"])

    def apply_to_widget(self, widget, **color_kwargs):
        """
        Apply theme colors to a widget.

        Args:
            widget: CustomTkinter widget
            **color_kwargs: Color mappings (e.g., fg_color="bg", text_color="fg")
        """
        theme_colors = self.get_theme_colors()

        for attr, color_key in color_kwargs.items():
            if color_key in theme_colors:
                try:
                    widget.configure(**{attr: theme_colors[color_key]})
                except Exception as e:
                    logger.warning(f"Failed to apply {attr} to widget: {e}")
