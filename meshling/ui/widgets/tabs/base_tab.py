"""Base tab widget for the enhanced UI architecture."""

from abc import ABCMeta, abstractmethod

from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static

from meshling.core.event_bus import EventType, event_bus
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class BaseTabMeta(type(Container), ABCMeta):
    """Metaclass that combines Container's metaclass with ABCMeta."""
    pass


class BaseTab(Container, metaclass=BaseTabMeta):
    """Abstract base class for all tab widgets."""

    # Reactive properties
    is_active = reactive(False)
    has_updates = reactive(False)

    def __init__(self, tab_id: str, title: str, **kwargs):
        super().__init__(**kwargs)
        self.tab_id = tab_id
        self.title = title
        self.add_class("tab-content")
        self._subscribed_events = []

    async def on_mount(self) -> None:
        """Initialize the tab when mounted."""
        await self.setup_event_subscriptions()
        await self.initialize_tab()

    async def on_unmount(self) -> None:
        """Clean up when tab is unmounted."""
        await self.cleanup_tab()
        self._unsubscribe_all()

    @abstractmethod
    async def initialize_tab(self) -> None:
        """Initialize tab-specific functionality."""
        pass

    @abstractmethod
    async def cleanup_tab(self) -> None:
        """Clean up tab-specific resources."""
        pass

    @abstractmethod
    async def setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for this tab."""
        pass

    @abstractmethod
    async def refresh_data(self) -> None:
        """Refresh tab data when activated."""
        pass

    def subscribe_to_event(self, event_type: EventType, callback) -> None:
        """Subscribe to an event and track the subscription."""
        event_bus.subscribe(event_type, callback)
        self._subscribed_events.append((event_type, callback))

    def _unsubscribe_all(self) -> None:
        """Unsubscribe from all tracked events."""
        for event_type, callback in self._subscribed_events:
            event_bus.unsubscribe(event_type, callback)
        self._subscribed_events.clear()

    async def on_tab_activated(self) -> None:
        """Called when this tab becomes active."""
        self.is_active = True
        self.has_updates = False

        # Only refresh data if the tab is mounted
        if self.is_mounted:
            await self.refresh_data()
        else:
            # Defer refresh until after mounting
            self.call_later(self.refresh_data)

        logger.debug(f"Tab {self.tab_id} activated")

    async def on_tab_deactivated(self) -> None:
        """Called when this tab becomes inactive."""
        self.is_active = False
        logger.debug(f"Tab {self.tab_id} deactivated")

    def mark_updated(self) -> None:
        """Mark this tab as having updates."""
        if not self.is_active:
            self.has_updates = True


class TabPlaceholder(Static):
    """Placeholder content for tabs under development."""

    def __init__(self, tab_name: str, **kwargs):
        content = f"[bold]{tab_name} Tab[/bold]\n\nThis tab is under development.\nFunctionality will be implemented in upcoming phases."
        super().__init__(content, **kwargs)
        self.add_class("tab-placeholder")
