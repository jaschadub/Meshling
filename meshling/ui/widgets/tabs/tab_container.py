"""Tab container widget for managing tab navigation."""

from typing import Dict, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from meshling.ui.widgets.tabs.base_tab import BaseTab
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class TabButton(Button):
    """Custom button for tab navigation."""

    def __init__(self, tab_id: str, title: str, **kwargs):
        super().__init__(title, **kwargs)
        self.tab_id = tab_id
        self.add_class("tab-button")

    def set_active(self, active: bool) -> None:
        """Set the active state of the tab button."""
        if active:
            self.add_class("tab-button-active")
            self.remove_class("tab-button-inactive")
        else:
            self.add_class("tab-button-inactive")
            self.remove_class("tab-button-active")

    def set_has_updates(self, has_updates: bool) -> None:
        """Set the update indicator for the tab button."""
        if has_updates:
            self.add_class("tab-button-updated")
        else:
            self.remove_class("tab-button-updated")


class TabBar(Horizontal):
    """Tab bar widget for tab navigation buttons."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("tab-bar")
        self._tab_buttons: Dict[str, TabButton] = {}

    def add_tab_button(self, tab_id: str, title: str) -> TabButton:
        """Add a tab button to the bar."""
        button = TabButton(tab_id, title, id=f"tab_button_{tab_id}")
        self._tab_buttons[tab_id] = button
        self.mount(button)
        return button

    def set_active_tab(self, tab_id: str) -> None:
        """Set the active tab button."""
        for tid, button in self._tab_buttons.items():
            button.set_active(tid == tab_id)

    def set_tab_updates(self, tab_id: str, has_updates: bool) -> None:
        """Set update indicator for a tab."""
        if tab_id in self._tab_buttons:
            self._tab_buttons[tab_id].set_has_updates(has_updates)


class TabContainer(Container):
    """Container widget that manages tab navigation and content."""

    active_tab = reactive("channels")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("tab-container")
        self._tabs: Dict[str, BaseTab] = {}
        self._tab_order: List[str] = []

    def compose(self) -> ComposeResult:
        """Compose the tab container layout."""
        yield TabBar(id="tab_bar")
        yield ContentSwitcher(initial="channels", id="tab_content")

    def add_tab(self, tab: BaseTab) -> None:
        """Add a tab to the container."""
        self._tabs[tab.tab_id] = tab
        self._tab_order.append(tab.tab_id)

        # Set the tab's ID to match its tab_id for ContentSwitcher
        tab.id = tab.tab_id

        # Add button to tab bar
        tab_bar = self.query_one("#tab_bar", TabBar)
        tab_bar.add_tab_button(tab.tab_id, tab.title)

        # Add tab content to switcher
        content_switcher = self.query_one("#tab_content", ContentSwitcher)
        content_switcher.mount(tab)

        logger.debug(f"Added tab: {tab.tab_id}")

    async def switch_to_tab(self, tab_id: str) -> None:
        """Switch to the specified tab."""
        if tab_id not in self._tabs:
            logger.warning(f"Tab {tab_id} not found")
            return

        # Deactivate current tab
        if self.active_tab in self._tabs:
            await self._tabs[self.active_tab].on_tab_deactivated()

        # Switch content
        content_switcher = self.query_one("#tab_content", ContentSwitcher)
        content_switcher.current = tab_id

        # Update tab bar
        tab_bar = self.query_one("#tab_bar", TabBar)
        tab_bar.set_active_tab(tab_id)

        # Activate new tab
        self.active_tab = tab_id
        await self._tabs[tab_id].on_tab_activated()

        logger.debug(f"Switched to tab: {tab_id}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle tab button presses."""
        if isinstance(event.button, TabButton):
            self.app.call_later(self.switch_to_tab, event.button.tab_id)

    def get_tab(self, tab_id: str) -> Optional[BaseTab]:
        """Get a tab by ID."""
        return self._tabs.get(tab_id)

    def mark_tab_updated(self, tab_id: str) -> None:
        """Mark a tab as having updates."""
        if tab_id in self._tabs:
            self._tabs[tab_id].mark_updated()
            tab_bar = self.query_one("#tab_bar", TabBar)
            tab_bar.set_tab_updates(tab_id, True)

    def get_next_tab_id(self) -> Optional[str]:
        """Get the next tab ID in order."""
        if not self._tab_order:
            return None

        try:
            current_index = self._tab_order.index(self.active_tab)
            next_index = (current_index + 1) % len(self._tab_order)
            return self._tab_order[next_index]
        except ValueError:
            return self._tab_order[0] if self._tab_order else None

    def get_previous_tab_id(self) -> Optional[str]:
        """Get the previous tab ID in order."""
        if not self._tab_order:
            return None

        try:
            current_index = self._tab_order.index(self.active_tab)
            prev_index = (current_index - 1) % len(self._tab_order)
            return self._tab_order[prev_index]
        except ValueError:
            return self._tab_order[-1] if self._tab_order else None

    async def on_key(self, event) -> None:
        """Handle keyboard shortcuts for tab navigation."""
        if event.key == "ctrl+tab":
            next_tab = self.get_next_tab_id()
            if next_tab:
                await self.switch_to_tab(next_tab)
                event.prevent_default()
        elif event.key == "ctrl+shift+tab":
            prev_tab = self.get_previous_tab_id()
            if prev_tab:
                await self.switch_to_tab(prev_tab)
                event.prevent_default()
        elif event.key.startswith("ctrl+") and event.key[-1].isdigit():
            # Ctrl+1-5 for direct tab access
            tab_num = int(event.key[-1]) - 1
            if 0 <= tab_num < len(self._tab_order):
                await self.switch_to_tab(self._tab_order[tab_num])
                event.prevent_default()
