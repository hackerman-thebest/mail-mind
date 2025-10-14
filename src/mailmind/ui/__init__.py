"""
MailMind UI Package

This package contains the desktop user interface built with CustomTkinter.
Implements Story 2.3: CustomTkinter UI Framework.

Components:
- theme_manager: Theme management (dark/light mode)
- main_window: Main application window
- components/: Reusable UI components
- dialogs/: Dialog windows
- controllers/: Business logic controllers
"""

from mailmind.ui.theme_manager import ThemeManager

__all__ = ['ThemeManager']
