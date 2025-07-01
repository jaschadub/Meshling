"""Main Textual application for Meshling TUI."""

import asyncio
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Log, Static

from meshling.core.connection_manager import ConnectionManager
from meshling.core.event_bus import Event, EventType, event_bus
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class PacketLogWidget(Log):
    """Widget for displaying packet log."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("packet-log")

    def add_packet(self, packet: dict) -> None:
        """Add a packet to the log display."""
        try:
            # Format packet for display
            from_node = packet.get('from', 'Unknown')
            to_node = packet.get('to', 'Broadcast')

            # Get text content if available
            decoded = packet.get('decoded', {})
            text = decoded.get('text', '')

            if text:
                # Text message
                self.write(f"[bold cyan]MSG[/bold cyan] {from_node} → {to_node}: {text}")
            else:
                # Other packet type
                portnum = decoded.get('portnum', 'Unknown')
                self.write(f"[bold yellow]PKT[/bold yellow] {from_node} → {to_node} ({portnum})")

            # Add metadata
            rx_snr = packet.get('rx_snr', 0)
            rx_rssi = packet.get('rx_rssi', 0)
            if rx_snr or rx_rssi:
                self.write(f"    [dim]SNR: {rx_snr}dB, RSSI: {rx_rssi}dBm[/dim]")

        except Exception as e:
            logger.error(f"Error formatting packet: {e}")
            self.write(f"[red]Error displaying packet: {e}[/red]")


class StatusPanel(Static):
    """Widget for displaying device status."""

    connection_status = reactive("Disconnected")
    device_type = reactive("None")
    firmware_version = reactive("Unknown")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("status-panel")

    def render(self) -> str:
        """Render the status panel content."""
        status_color = {
            "Connected": "green",
            "Connecting": "yellow",
            "Disconnected": "red",
            "Failed": "red"
        }.get(self.connection_status, "white")

        return f"""[bold]Connection:[/bold] [{status_color}]{self.connection_status}[/{status_color}]
[bold]Device Type:[/bold] {self.device_type}
[bold]Firmware:[/bold] {self.firmware_version}
[bold]Nodes:[/bold] 0"""

    def update_status(self, status: str, device_info: Optional[dict] = None) -> None:
        """Update the status display."""
        self.connection_status = status

        if device_info:
            self.device_type = device_info.get('type', 'Unknown')
            self.firmware_version = device_info.get('firmware_version', 'Unknown')


class MessageInput(Container):
    """Widget for message input and sending."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("message-input")

    def compose(self) -> ComposeResult:
        """Compose the message input widget."""
        yield Input(placeholder="Type your message...", id="message_input")
        yield Button("Send", variant="success", id="send_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle send button press."""
        if event.button.id == "send_button":
            self.send_message()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "message_input":
            self.send_message()

    def send_message(self) -> None:
        """Send the message."""
        input_widget = self.query_one("#message_input", Input)
        message = input_widget.value.strip()

        if message:
            # Emit message send event
            asyncio.create_task(event_bus.emit(EventType.MESSAGE_SEND_REQUESTED, {
                'text': message
            }))

            # Clear input
            input_widget.value = ""


class ConnectionPanel(Container):
    """Widget for connection controls."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class("connection-panel")
        self.is_connected = False

    def compose(self) -> ComposeResult:
        """Compose the connection panel widget."""
        yield Button("Auto Connect", variant="success", id="auto_connect_button")
        yield Button("Disconnect", variant="error", id="disconnect_button", disabled=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "auto_connect_button":
            self.app.call_later(self.app.connection_manager.auto_connect)
        elif event.button.id == "disconnect_button":
            self.app.call_later(self.app.connection_manager.disconnect)

    def update_connection_state(self, connected: bool) -> None:
        """Update button states based on connection."""
        self.is_connected = connected

        auto_button = self.query_one("#auto_connect_button", Button)
        disconnect_button = self.query_one("#disconnect_button", Button)

        auto_button.disabled = connected
        disconnect_button.disabled = not connected


class MeshlingApp(App):
    """Main Meshling TUI application."""

    CSS_PATH = "ui/styles/main.tcss"
    TITLE = "Meshling - Meshtastic TUI"

    def __init__(self, serial_port: Optional[str] = None,
                 tcp_host: Optional[str] = None, tcp_port: int = 4403):
        super().__init__()
        self.connection_manager = ConnectionManager()
        self.serial_port = serial_port
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header(show_clock=True)

        with Container(classes="main-content"):
            # Left side - packet log
            yield PacketLogWidget(id="packet_log")

            # Right side - controls
            with Vertical(classes="right-panel"):
                yield StatusPanel(id="status_panel")
                yield MessageInput(id="message_input")
                yield ConnectionPanel(id="connection_panel")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the application."""
        logger.info("Starting Meshling TUI")

        # Start event bus
        await event_bus.start()

        # Subscribe to events
        event_bus.subscribe(EventType.PACKET_RECEIVED, self._on_packet_received)
        event_bus.subscribe(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        event_bus.subscribe(EventType.CONNECTION_LOST, self._on_connection_lost)
        event_bus.subscribe(EventType.CONNECTION_FAILED, self._on_connection_failed)
        event_bus.subscribe(EventType.MESSAGE_SEND_REQUESTED, self._on_message_send_requested)
        event_bus.subscribe(EventType.DEVICE_STATUS_CHANGED, self._on_device_status_changed)

        # Auto-connect if parameters provided
        if self.serial_port:
            await self.connection_manager.connect_serial(self.serial_port)
        elif self.tcp_host:
            await self.connection_manager.connect_tcp(self.tcp_host, self.tcp_port)
        else:
            # Show welcome message
            packet_log = self.query_one("#packet_log", PacketLogWidget)
            packet_log.write("[bold green]Welcome to Meshling![/bold green]")
            packet_log.write("Click 'Auto Connect' to find and connect to a Meshtastic device.")

    async def on_unmount(self) -> None:
        """Clean up when application exits."""
        logger.info("Shutting down Meshling TUI")

        # Disconnect from device
        await self.connection_manager.disconnect()

        # Stop event bus
        await event_bus.stop()

    def _on_packet_received(self, event: Event) -> None:
        """Handle received packet events."""
        packet = event.data.get('packet', {})
        packet_log = self.query_one("#packet_log", PacketLogWidget)
        packet_log.add_packet(packet)

    def _on_connection_established(self, event: Event) -> None:
        """Handle connection established events."""
        device_info = event.data.get('device_info', {})
        interface_type = event.data.get('interface_type', 'unknown')

        # Update status panel
        status_panel = self.query_one("#status_panel", StatusPanel)
        status_panel.update_status("Connected", device_info)

        # Update connection panel
        connection_panel = self.query_one("#connection_panel", ConnectionPanel)
        connection_panel.update_connection_state(True)

        # Log connection
        packet_log = self.query_one("#packet_log", PacketLogWidget)
        packet_log.write(f"[bold green]Connected via {interface_type}[/bold green]")

    def _on_connection_lost(self, event: Event) -> None:
        """Handle connection lost events."""
        reason = event.data.get('reason', 'unknown')

        # Update status panel
        status_panel = self.query_one("#status_panel", StatusPanel)
        status_panel.update_status("Disconnected")

        # Update connection panel
        connection_panel = self.query_one("#connection_panel", ConnectionPanel)
        connection_panel.update_connection_state(False)

        # Log disconnection
        packet_log = self.query_one("#packet_log", PacketLogWidget)
        packet_log.write(f"[bold red]Disconnected ({reason})[/bold red]")

    def _on_connection_failed(self, event: Event) -> None:
        """Handle connection failed events."""
        error = event.data.get('error', 'unknown error')

        # Update status panel
        status_panel = self.query_one("#status_panel", StatusPanel)
        status_panel.update_status("Failed")

        # Update connection panel
        connection_panel = self.query_one("#connection_panel", ConnectionPanel)
        connection_panel.update_connection_state(False)

        # Log error
        packet_log = self.query_one("#packet_log", PacketLogWidget)
        packet_log.write(f"[bold red]Connection failed: {error}[/bold red]")

    async def _on_message_send_requested(self, event: Event) -> None:
        """Handle message send requests."""
        text = event.data.get('text', '')

        if text:
            success = await self.connection_manager.send_message(text)

            packet_log = self.query_one("#packet_log", PacketLogWidget)
            if success:
                packet_log.write(f"[bold blue]SENT[/bold blue] You: {text}")
            else:
                packet_log.write(f"[bold red]FAILED[/bold red] Could not send: {text}")

    def _on_device_status_changed(self, event: Event) -> None:
        """Handle device status change events."""
        status = event.data.get('status', 'unknown')

        # Update status panel
        status_panel = self.query_one("#status_panel", StatusPanel)

        # Map status to display string
        status_map = {
            'connected': 'Connected',
            'connecting': 'Connecting',
            'disconnected': 'Disconnected',
            'failed': 'Failed',
            'reconnecting': 'Reconnecting'
        }

        display_status = status_map.get(status, status.title())
        status_panel.connection_status = display_status
