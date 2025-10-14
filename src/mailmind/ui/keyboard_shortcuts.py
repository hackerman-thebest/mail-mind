"""
Keyboard Shortcuts Module

Implements Story 2.3 AC8: Keyboard shortcuts for common actions
Defines all keyboard shortcuts and provides binding utilities.
"""

import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)


# Keyboard shortcut definitions
SHORTCUTS = {
    "<Control-r>": {
        "action": "refresh_email_list",
        "description": "Refresh email list"
    },
    "<Control-a>": {
        "action": "analyze_selected",
        "description": "Analyze selected email(s) now"
    },
    "<Control-n>": {
        "action": "compose_new",
        "description": "Compose new email"
    },
    "<Control-Return>": {
        "action": "send_email",
        "description": "Send email (when in compose mode)"
    },
    "<Control-d>": {
        "action": "delete_selected",
        "description": "Delete selected email(s)"
    },
    "<Control-m>": {
        "action": "move_selected",
        "description": "Move selected email to folder"
    },
    "<Control-comma>": {
        "action": "open_settings",
        "description": "Open Settings dialog"
    },
    "<Control-t>": {
        "action": "toggle_theme",
        "description": "Toggle theme (dark/light)"
    },
    "<Control-slash>": {
        "action": "show_shortcuts",
        "description": "Show keyboard shortcuts cheat sheet"
    },
    "<Escape>": {
        "action": "close_dialog",
        "description": "Close dialogs or deselect"
    }
}


def bind_shortcuts(window, handlers: Dict[str, Callable]):
    """
    Bind keyboard shortcuts to window.

    Args:
        window: Window to bind shortcuts to
        handlers: Dict mapping action names to handler functions
    """
    for key_combo, shortcut_info in SHORTCUTS.items():
        action = shortcut_info["action"]

        if action in handlers:
            window.bind(key_combo, lambda e, a=action: _handle_shortcut(a, handlers))
            logger.debug(f"Bound shortcut: {key_combo} -> {action}")


def _handle_shortcut(action: str, handlers: Dict[str, Callable]):
    """
    Handle keyboard shortcut.

    Args:
        action: Action name
        handlers: Handler functions dict
    """
    if action in handlers:
        try:
            handlers[action]()
            logger.debug(f"Executed shortcut action: {action}")
        except Exception as e:
            logger.error(f"Shortcut action failed: {action} - {e}")


def get_shortcuts_text() -> str:
    """
    Get formatted keyboard shortcuts text for display.

    Returns:
        Formatted text listing all shortcuts
    """
    lines = ["Keyboard Shortcuts:", ""]

    for key_combo, info in SHORTCUTS.items():
        # Format key combo for display
        display_key = key_combo.replace("<Control-", "Ctrl+")
        display_key = display_key.replace("<", "").replace(">", "")
        display_key = display_key.replace("Return", "Enter")
        display_key = display_key.replace("comma", ",")
        display_key = display_key.replace("slash", "/")

        lines.append(f"{display_key:20s} - {info['description']}")

    return "\n".join(lines)
