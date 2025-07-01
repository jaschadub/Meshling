"""Packets tab for detailed packet monitoring and analysis."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Log, Static

from meshling.core.event_bus import Event, EventType
from meshling.ui.widgets.tabs.base_tab import BaseTab
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class PacketsTab(BaseTab):
    """Tab for monitoring and analyzing mesh packets."""

    def __init__(self, **kwargs):
        super().__init__("packets", "Packets", **kwargs)
        self._packet_count = 0

    def compose(self) -> ComposeResult:
        """Compose the packets tab layout."""
        with Vertical():
            # Header with packet statistics
            with Container(classes="packets-header"):
                yield Static("Packet Monitor", classes="tab-title")
                yield Static("Real-time packet monitoring and analysis", classes="tab-subtitle")
                yield Static("Packets: 0", id="packet_count", classes="packet-stats")

            # Main content area
            with Horizontal(classes="packets-content"):
                # Packet log (left side)
                with Container(classes="packet-log-container"):
                    yield Static("Live Packet Log", classes="section-title")
                    packet_log = Log(id="packet_log")
                    packet_log.markup = True
                    packet_log.highlight = True
                    yield packet_log

                # Packet details (right side)
                with Vertical(classes="packet-details"):
                    yield Static("Packet Details", classes="section-title")
                    packet_table = DataTable(id="packet_details_table")
                    packet_table.add_columns("Field", "Value")
                    yield packet_table

            # Control buttons
            with Horizontal(classes="packets-actions"):
                yield Button("Clear Log", id="clear_log_btn")
                yield Button("Export Log", id="export_log_btn")
                yield Button("Pause", id="pause_log_btn")
                yield Button("Filter", id="filter_packets_btn")

    async def initialize_tab(self) -> None:
        """Initialize the packets tab."""
        logger.debug("Initializing packets tab")
        # Don't query widgets here - wait for refresh_data to be called

    async def cleanup_tab(self) -> None:
        """Clean up packets tab resources."""
        logger.debug("Cleaning up packets tab")

    async def setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for packets."""
        self.subscribe_to_event(EventType.PACKET_RECEIVED, self._on_packet_received)
        self.subscribe_to_event(EventType.PACKET_SENT, self._on_packet_sent)
        self.subscribe_to_event(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        self.subscribe_to_event(EventType.CONNECTION_LOST, self._on_connection_lost)

    async def refresh_data(self) -> None:
        """Refresh packet data."""
        try:
            # Update packet count display
            count_widget = self.query_one("#packet_count", Static)
            count_widget.update(f"Packets: {self._packet_count}")

            # Initialize packet log if this is the first refresh
            packet_log = self.query_one("#packet_log", Log)
            if len(packet_log.lines) == 0:
                packet_log.write("[bold green]Welcome to Meshling![/bold green]")
                packet_log.write("Use the Connect button to find and connect to a Meshtastic device.")
                packet_log.write("[bold green]Packet monitoring started[/bold green]")
        except Exception as e:
            logger.debug(f"Could not refresh packet data: {e}")

    def _on_packet_received(self, event: Event) -> None:
        """Handle received packet events."""
        packet = event.data.get('packet', {})
        self._add_packet_to_log(packet, "RECV")
        self._update_packet_details(packet)

    def _on_packet_sent(self, event: Event) -> None:
        """Handle sent packet events."""
        packet = event.data.get('packet', {})
        self._add_packet_to_log(packet, "SENT")

    def _on_connection_established(self, event: Event) -> None:
        """Handle connection established event."""
        packet_log = self.query_one("#packet_log", Log)
        interface_type = event.data.get('interface_type', 'unknown')
        packet_log.write(f"[bold green]Connected via {interface_type}[/bold green]")

    def _on_connection_lost(self, event: Event) -> None:
        """Handle connection lost event."""
        packet_log = self.query_one("#packet_log", Log)
        reason = event.data.get('reason', 'unknown')
        packet_log.write(f"[bold red]Disconnected ({reason})[/bold red]")

    def _add_packet_to_log(self, packet: dict, direction: str) -> None:
        """Add a packet to the log display."""
        try:
            packet_log = self.query_one("#packet_log", Log)

            # Format packet for display
            from_node = packet.get('from', 'Unknown')
            to_node = packet.get('to', 'Broadcast')

            # Get decoded content
            decoded = packet.get('decoded', {})
            text = decoded.get('text', '')
            portnum = decoded.get('portnum', 'Unknown')

            # Direction indicator
            direction_color = "cyan" if direction == "RECV" else "blue"

            if text:
                # Text message
                packet_log.write(f"[bold {direction_color}]{direction}[/bold {direction_color}] {from_node} → {to_node}: {text}")
            else:
                # Other packet type
                packet_log.write(f"[bold {direction_color}]{direction}[/bold {direction_color}] {from_node} → {to_node} ({portnum})")

            # Add signal info if available
            rx_snr = packet.get('rx_snr', 0)
            rx_rssi = packet.get('rx_rssi', 0)
            if rx_snr or rx_rssi:
                packet_log.write(f"    [dim]SNR: {rx_snr}dB, RSSI: {rx_rssi}dBm[/dim]")

            # Update packet count
            self._packet_count += 1
            self.app.call_later(self.refresh_data)

        except Exception as e:
            logger.error(f"Error formatting packet: {e}")
            packet_log = self.query_one("#packet_log", Log)
            packet_log.write(f"[red]Error displaying packet: {e}[/red]")

    def _update_packet_details(self, packet: dict) -> None:
        """Update the packet details table."""
        try:
            table = self.query_one("#packet_details_table", DataTable)
            table.clear()

            # Add packet fields to details table
            table.add_row("From", str(packet.get('from', 'Unknown')))
            table.add_row("To", str(packet.get('to', 'Broadcast')))
            table.add_row("ID", str(packet.get('id', 'Unknown')))
            table.add_row("RX Time", str(packet.get('rx_time', 'Unknown')))
            table.add_row("RX SNR", f"{packet.get('rx_snr', 0)}dB")
            table.add_row("RX RSSI", f"{packet.get('rx_rssi', 0)}dBm")
            table.add_row("Hop Limit", str(packet.get('hop_limit', 'Unknown')))

            # Add decoded fields if available
            decoded = packet.get('decoded', {})
            if decoded:
                table.add_row("Port", str(decoded.get('portnum', 'Unknown')))
                if 'text' in decoded:
                    table.add_row("Text", decoded['text'])

        except Exception as e:
            logger.error(f"Error updating packet details: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the packets tab."""
        if event.button.id == "clear_log_btn":
            self._clear_log()
        elif event.button.id == "export_log_btn":
            self._export_log()
        elif event.button.id == "pause_log_btn":
            self._toggle_pause()
        elif event.button.id == "filter_packets_btn":
            self._show_filter_dialog()

    def _clear_log(self) -> None:
        """Clear the packet log."""
        packet_log = self.query_one("#packet_log", Log)
        packet_log.clear()
        self._packet_count = 0
        self.app.call_later(self.refresh_data)
        packet_log.write("[bold yellow]Log cleared[/bold yellow]")

    def _export_log(self) -> None:
        """Export the packet log."""
        # TODO: Implement log export functionality
        logger.info("Export log requested")

    def _toggle_pause(self) -> None:
        """Toggle packet log pause."""
        # TODO: Implement pause functionality
        logger.info("Toggle pause requested")

    def _show_filter_dialog(self) -> None:
        """Show packet filter dialog."""
        # TODO: Implement filter dialog
        logger.info("Filter dialog requested")
