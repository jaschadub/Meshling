"""Event bus system for loose coupling between components."""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """Event types for the application."""

    # Connection events
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_FAILED = "connection_failed"

    # Packet events
    PACKET_RECEIVED = "packet_received"
    PACKET_SENT = "packet_sent"
    PACKET_FAILED = "packet_failed"

    # Device events
    DEVICE_STATUS_CHANGED = "device_status_changed"
    DEVICE_CONFIG_CHANGED = "device_config_changed"

    # Node events
    NODE_DISCOVERED = "node_discovered"
    NODE_UPDATED = "node_updated"
    NODE_LOST = "node_lost"

    # Channel events
    CHANNEL_CONFIG_CHANGED = "channel_config_changed"
    CHANNEL_ADDED = "channel_added"
    CHANNEL_REMOVED = "channel_removed"

    # Message events
    MESSAGE_SEND_REQUESTED = "message_send_requested"
    MESSAGE_SEND_FAILED = "message_send_failed"
    MESSAGE_RECEIVED = "message_received"

    # Configuration events
    CONFIG_LOADED = "config_loaded"
    CONFIG_SAVED = "config_saved"
    CONFIG_RESET = "config_reset"

    # UI events
    UI_ERROR = "ui_error"
    TAB_ACTIVATED = "tab_activated"
    TAB_DEACTIVATED = "tab_deactivated"

    # Application events
    APP_SHUTDOWN = "app_shutdown"


class Event:
    """Event data container."""

    def __init__(self, event_type: EventType, data: Optional[Dict[str, Any]] = None):
        self.type = event_type
        self.data = data or {}
        self.timestamp = asyncio.get_event_loop().time()

    def __repr__(self) -> str:
        return f"Event(type={self.type.value}, data={self.data})"


class EventBus:
    """Async event bus for component communication."""

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._running = False
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the event bus processor."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.debug("Event bus started")

    async def stop(self) -> None:
        """Stop the event bus processor."""
        if not self._running:
            return

        self._running = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        logger.debug("Event bus stopped")

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type.value}")
            except ValueError:
                pass

    async def emit(self, event_type: EventType, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event.

        Args:
            event_type: Type of event to emit
            data: Optional event data
        """
        event = Event(event_type, data)
        await self._event_queue.put(event)
        logger.debug(f"Emitted event: {event}")

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                # Wait for event with timeout to allow clean shutdown
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _handle_event(self, event: Event) -> None:
        """Handle a single event by calling all subscribers.

        Args:
            event: Event to handle
        """
        subscribers = self._subscribers.get(event.type, [])

        if not subscribers:
            logger.debug(f"No subscribers for event: {event.type.value}")
            return

        # Call all subscribers
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback for {event.type.value}: {e}")


# Global event bus instance
event_bus = EventBus()
