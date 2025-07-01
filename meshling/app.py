"""Main Textual application for Meshling TUI."""

from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer

from meshling.core.connection_manager import ConnectionManager
from meshling.core.event_bus import Event, EventType, event_bus
from meshling.ui.widgets import (
    ChannelsTab,
    ConfigTab,
    EnhancedHeader,
    MessagesTab,
    NodesTab,
    PacketsTab,
    TabContainer,
)
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class MeshlingApp(App):
    """Main Meshling TUI application with enhanced tab-based interface."""

    CSS_PATH = "ui/styles/main.tcss"
    TITLE = "Meshling - Meshtastic TUI"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+tab", "next_tab", "Next Tab"),
        ("ctrl+shift+tab", "prev_tab", "Previous Tab"),
        ("ctrl+1", "tab_channels", "Channels"),
        ("ctrl+2", "tab_nodes", "Nodes"),
        ("ctrl+3", "tab_packets", "Packets"),
        ("ctrl+4", "tab_config", "Config"),
        ("ctrl+5", "tab_messages", "Messages"),
    ]

    def __init__(self, serial_port: Optional[str] = None,
                 tcp_host: Optional[str] = None, tcp_port: int = 4403):
        super().__init__()
        self.connection_manager = ConnectionManager()
        self.serial_port = serial_port
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self._node_update_timer = None

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        # Enhanced header with device info and controls
        yield EnhancedHeader(id="enhanced_header")

        # Main content area with tabs
        with Container(classes="main-content"):
            yield TabContainer(id="tab_container")

        # Footer with keybindings
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the application."""
        logger.info("Starting Meshling TUI with enhanced interface")

        # Start event bus
        await event_bus.start()

        # Subscribe to events
        event_bus.subscribe(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        event_bus.subscribe(EventType.CONNECTION_LOST, self._on_connection_lost)
        event_bus.subscribe(EventType.CONNECTION_FAILED, self._on_connection_failed)

        # Initialize tabs
        await self._setup_tabs()

        # Auto-connect if parameters provided
        if self.serial_port:
            await self.connection_manager.connect_serial(self.serial_port)
        elif self.tcp_host:
            await self.connection_manager.connect_tcp(self.tcp_host, self.tcp_port)
        else:
            # Welcome message will be shown when packets tab is activated
            logger.info("No connection parameters provided - waiting for manual connection")

    async def on_unmount(self) -> None:
        """Clean up when application exits."""
        logger.info("Shutting down Meshling TUI")

        # Stop node update timer
        if self._node_update_timer:
            self._node_update_timer.stop()

        # Disconnect from device
        await self.connection_manager.disconnect()

        # Stop event bus
        await event_bus.stop()

    async def _setup_tabs(self) -> None:
        """Set up all application tabs."""
        tab_container = self.query_one("#tab_container", TabContainer)

        # Create and add tabs in order
        tabs = [
            ChannelsTab(),
            NodesTab(),
            PacketsTab(),
            ConfigTab(),
            MessagesTab(),
        ]

        for tab in tabs:
            tab_container.add_tab(tab)

        # Switch to channels tab by default
        await tab_container.switch_to_tab("channels")

    def _on_connection_established(self, event: Event) -> None:
        """Handle connection established events."""
        interface_type = event.data.get('interface_type', 'unknown')

        logger.info(f"Connected via {interface_type}")

        # Start node info updater
        if self._node_update_timer:
            self._node_update_timer.stop()
        self._node_update_timer = self.set_interval(10.0, self._update_node_info)

    def _on_connection_lost(self, event: Event) -> None:
        """Handle connection lost events."""
        reason = event.data.get('reason', 'unknown')
        logger.info(f"Disconnected ({reason})")

        # Stop node info updater
        if self._node_update_timer:
            self._node_update_timer.stop()

    def _on_connection_failed(self, event: Event) -> None:
        """Handle connection failed events."""
        error = event.data.get('error', 'unknown error')
        logger.warning(f"Connection failed: {error}")

    async def _update_node_info(self) -> None:
        """Periodically update node information."""
        if self.connection_manager.is_connected:
            try:
                node_info = await self.connection_manager.get_node_info()
                node_count = len(node_info)

                # Update header with node count
                header = self.query_one("#enhanced_header", EnhancedHeader)
                await header.update_node_count(node_count)

            except Exception as e:
                logger.error(f"Failed to update node info: {e}")

    # Action methods for keybindings
    async def action_next_tab(self) -> None:
        """Switch to next tab."""
        tab_container = self.query_one("#tab_container", TabContainer)
        next_tab = tab_container.get_next_tab_id()
        if next_tab:
            await tab_container.switch_to_tab(next_tab)

    async def action_prev_tab(self) -> None:
        """Switch to previous tab."""
        tab_container = self.query_one("#tab_container", TabContainer)
        prev_tab = tab_container.get_previous_tab_id()
        if prev_tab:
            await tab_container.switch_to_tab(prev_tab)

    async def action_tab_channels(self) -> None:
        """Switch to channels tab."""
        tab_container = self.query_one("#tab_container", TabContainer)
        await tab_container.switch_to_tab("channels")

    async def action_tab_nodes(self) -> None:
        """Switch to nodes tab."""
        tab_container = self.query_one("#tab_container", TabContainer)
        await tab_container.switch_to_tab("nodes")

    async def action_tab_packets(self) -> None:
        """Switch to packets tab."""
        tab_container = self.query_one("#tab_container", TabContainer)
        await tab_container.switch_to_tab("packets")

    async def action_tab_config(self) -> None:
        """Switch to config tab."""
        tab_container = self.query_one("#tab_container", TabContainer)
        await tab_container.switch_to_tab("config")

    async def action_tab_messages(self) -> None:
        """Switch to messages tab."""
        tab_container = self.query_one("#tab_container", TabContainer)
        await tab_container.switch_to_tab("messages")
