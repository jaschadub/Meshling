"""Enhanced header widget with device information and status."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Static

from meshling.core.event_bus import Event, EventType, event_bus
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class DeviceStatusWidget(Static):
    """Widget displaying device connection status and info."""

    connection_status = reactive("Disconnected")
    device_type = reactive("None")
    firmware_version = reactive("Unknown")
    node_count = reactive(0)
    signal_quality = reactive("--")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("device-status")

    def render(self) -> str:
        """Render the device status content."""
        status_color = {
            "Connected": "green",
            "Connecting": "yellow",
            "Disconnected": "red",
            "Failed": "red"
        }.get(self.connection_status, "white")

        return f"""[bold]Status:[/bold] [{status_color}]{self.connection_status}[/{status_color}] | [bold]Device:[/bold] {self.device_type} | [bold]FW:[/bold] {self.firmware_version} | [bold]Nodes:[/bold] {self.node_count} | [bold]Signal:[/bold] {self.signal_quality}"""

    def update_status(self, status: str, device_info: dict = None) -> None:
        """Update the device status display."""
        self.connection_status = status

        if device_info:
            self.device_type = device_info.get('type', 'Unknown')
            self.firmware_version = device_info.get('firmware_version', 'Unknown')

    def update_signal_quality(self, snr: float = None, rssi: float = None) -> None:
        """Update signal quality display."""
        if snr is not None and rssi is not None:
            self.signal_quality = f"SNR:{snr}dB RSSI:{rssi}dBm"
        else:
            self.signal_quality = "--"


class ConnectionControls(Container):
    """Widget for connection control buttons."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("connection-controls")
        self.is_connected = False

    def compose(self) -> ComposeResult:
        """Compose the connection controls."""
        from textual.widgets import Button

        with Horizontal():
            yield Button("Connect", variant="success", id="connect_btn", classes="header-button")
            yield Button("Disconnect", variant="error", id="disconnect_btn", disabled=True, classes="header-button")

    def update_connection_state(self, connected: bool) -> None:
        """Update button states based on connection."""
        self.is_connected = connected

        try:
            connect_btn = self.query_one("#connect_btn")
            disconnect_btn = self.query_one("#disconnect_btn")

            connect_btn.disabled = connected
            disconnect_btn.disabled = not connected
        except Exception as e:
            logger.error(f"Error updating connection controls: {e}")

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "connect_btn":
            self.app.call_later(self.app.connection_manager.auto_connect)
        elif event.button.id == "disconnect_btn":
            self.app.call_later(self.app.connection_manager.disconnect)


class EnhancedHeader(Container):
    """Enhanced header widget with device info and controls."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("enhanced-header")

    def compose(self) -> ComposeResult:
        """Compose the enhanced header layout."""
        with Horizontal():
            # App title
            yield Static("Meshling - Meshtastic TUI", classes="app-title")

            # Device status (center)
            yield DeviceStatusWidget(id="device_status")

            # Connection controls (right)
            yield ConnectionControls(id="connection_controls")

    async def on_mount(self) -> None:
        """Initialize header when mounted."""
        # Subscribe to relevant events
        event_bus.subscribe(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        event_bus.subscribe(EventType.CONNECTION_LOST, self._on_connection_lost)
        event_bus.subscribe(EventType.CONNECTION_FAILED, self._on_connection_failed)
        event_bus.subscribe(EventType.DEVICE_STATUS_CHANGED, self._on_device_status_changed)
        event_bus.subscribe(EventType.PACKET_RECEIVED, self._on_packet_received)

    def _on_connection_established(self, event: Event) -> None:
        """Handle connection established events."""
        device_info = event.data.get('device_info', {})

        # Update device status
        device_status = self.query_one("#device_status", DeviceStatusWidget)
        device_status.update_status("Connected", device_info)

        # Update connection controls
        connection_controls = self.query_one("#connection_controls", ConnectionControls)
        connection_controls.update_connection_state(True)

    def _on_connection_lost(self, event: Event) -> None:
        """Handle connection lost events."""
        # Update device status
        device_status = self.query_one("#device_status", DeviceStatusWidget)
        device_status.update_status("Disconnected")
        device_status.update_signal_quality()

        # Update connection controls
        connection_controls = self.query_one("#connection_controls", ConnectionControls)
        connection_controls.update_connection_state(False)

    def _on_connection_failed(self, event: Event) -> None:
        """Handle connection failed events."""
        # Update device status
        device_status = self.query_one("#device_status", DeviceStatusWidget)
        device_status.update_status("Failed")

        # Update connection controls
        connection_controls = self.query_one("#connection_controls", ConnectionControls)
        connection_controls.update_connection_state(False)

    def _on_device_status_changed(self, event: Event) -> None:
        """Handle device status change events."""
        status = event.data.get('status', 'unknown')
        device_info = event.data.get('device_info', {})

        # Map status to display string
        status_map = {
            'connected': 'Connected',
            'connecting': 'Connecting',
            'disconnected': 'Disconnected',
            'failed': 'Failed',
            'reconnecting': 'Reconnecting'
        }

        display_status = status_map.get(status, status.title())
        device_status = self.query_one("#device_status", DeviceStatusWidget)
        device_status.update_status(display_status, device_info)

    def _on_packet_received(self, event: Event) -> None:
        """Handle packet received events to update signal quality."""
        packet = event.data.get('packet', {})
        snr = packet.get('rx_snr')
        rssi = packet.get('rx_rssi')

        if snr is not None or rssi is not None:
            device_status = self.query_one("#device_status", DeviceStatusWidget)
            device_status.update_signal_quality(snr, rssi)

    async def update_node_count(self, count: int) -> None:
        """Update the node count display."""
        device_status = self.query_one("#device_status", DeviceStatusWidget)
        device_status.node_count = count
