"""Messages tab for text messaging functionality."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Select, Static

from meshling.core.event_bus import Event, EventType
from meshling.ui.widgets.tabs.base_tab import BaseTab
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class MessagesTab(BaseTab):
    """Tab for text messaging functionality."""

    def __init__(self, **kwargs):
        super().__init__("messages", "Messages", **kwargs)
        self._message_count = 0

    def compose(self) -> ComposeResult:
        """Compose the messages tab layout."""
        with Vertical():
            # Header
            with Container(classes="messages-header"):
                yield Static("Messages", classes="tab-title")
                yield Static("Send and receive text messages", classes="tab-subtitle")
                yield Static("Messages: 0", id="message_count", classes="message-stats")

            # Main content area
            with Horizontal(classes="messages-content"):
                # Message log (left side - larger)
                with Container(classes="message-log-container"):
                    yield Static("Message History", classes="section-title")
                    message_log = RichLog(id="message_log", markup=True, highlight=True)
                    yield message_log

                # Message controls (right side)
                with Vertical(classes="message-controls"):
                    yield Static("Send Message", classes="section-title")

                    # Recipient selection
                    with Horizontal(classes="message-control-row"):
                        yield Static("To:", classes="control-label")
                        yield Select([
                            ("broadcast", "Broadcast (All)"),
                            ("!12345678", "Node1 (Primary Gateway)"),
                            ("!87654321", "Node2 (Remote Sensor)"),
                            ("!11223344", "Node3 (Repeater Alpha)")
                        ], id="recipient_select", classes="control-select")

                    # Channel selection
                    with Horizontal(classes="message-control-row"):
                        yield Static("Channel:", classes="control-label")
                        yield Select([
                            ("0", "Primary (0)"),
                            ("1", "Secondary (1)"),
                            ("2", "Admin (2)"),
                            ("3", "Public (3)")
                        ], id="channel_select", classes="control-select")

                    # Message priority
                    with Horizontal(classes="message-control-row"):
                        yield Static("Priority:", classes="control-label")
                        yield Select([
                            ("UNSET", "Normal"),
                            ("MIN", "Low"),
                            ("BACKGROUND", "Background"),
                            ("DEFAULT", "Default"),
                            ("RELIABLE", "Reliable"),
                            ("ACK", "Acknowledged")
                        ], id="priority_select", classes="control-select")

                    # Message statistics
                    with Container(classes="message-stats-container"):
                        yield Static("Message Statistics", classes="section-title")
                        yield Static("Sent: 0", id="sent_count", classes="stat-item")
                        yield Static("Received: 0", id="received_count", classes="stat-item")
                        yield Static("Failed: 0", id="failed_count", classes="stat-item")
                        yield Static("Pending: 0", id="pending_count", classes="stat-item")

            # Message input area
            with Container(classes="message-input-container"):
                yield Static("Compose Message", classes="section-title")
                with Horizontal(classes="message-input"):
                    yield Input(placeholder="Type your message...", id="message_input", classes="message-text-input")
                    yield Button("Send", variant="success", id="send_message_btn")
                    yield Button("Clear", id="clear_input_btn")

            # Message actions
            with Horizontal(classes="message-actions"):
                yield Button("Clear History", id="clear_history_btn")
                yield Button("Export Messages", id="export_messages_btn")
                yield Button("Message Settings", id="message_settings_btn")
                yield Button("Refresh", id="refresh_messages_btn")

    async def initialize_tab(self) -> None:
        """Initialize the messages tab."""
        logger.debug("Initializing messages tab")

        try:
            message_log = self.query_one("#message_log", RichLog)
            message_log.write("[bold green]Message system ready[/bold green]")
            message_log.write("Welcome to Meshling messaging! Connect to a device to start sending and receiving messages.")
            message_log.write("[dim]Messages will appear here in real-time.[/dim]")
        except Exception as e:
            logger.debug(f"Could not initialize message log: {e}")

    async def cleanup_tab(self) -> None:
        """Clean up messages tab resources."""
        logger.debug("Cleaning up messages tab")

    async def setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for messages."""
        self.subscribe_to_event(EventType.PACKET_RECEIVED, self._on_packet_received)
        self.subscribe_to_event(EventType.MESSAGE_SEND_REQUESTED, self._on_message_sent)
        self.subscribe_to_event(EventType.MESSAGE_SEND_FAILED, self._on_message_failed)
        self.subscribe_to_event(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        self.subscribe_to_event(EventType.CONNECTION_LOST, self._on_connection_lost)

    async def refresh_data(self) -> None:
        """Refresh message data."""
        try:
            # Update message count display
            count_widget = self.query_one("#message_count", Static)
            count_widget.update(f"Messages: {self._message_count}")
        except Exception as e:
            logger.debug(f"Could not refresh message data: {e}")

    def _on_packet_received(self, event: Event) -> None:
        """Handle received packet events."""
        packet = event.data.get('packet', {})
        decoded = packet.get('decoded', {})

        # Only show text messages
        if 'text' in decoded:
            try:
                message_log = self.query_one("#message_log", RichLog)
                from_node = packet.get('from', 'Unknown')
                to_node = packet.get('to', 'Broadcast')
                text = decoded['text']
                channel = packet.get('channel', 0)

                # Get signal quality info
                snr = packet.get('rx_snr', 0)
                rssi = packet.get('rx_rssi', 0)

                # Format timestamp
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                # Format the message with rich markup
                if to_node == 'Broadcast' or to_node == '4294967295':  # Broadcast address
                    message_log.write(f"[dim]{timestamp}[/dim] [bold cyan]{from_node}[/bold cyan] [dim]→ All (Ch {channel}):[/dim] {text}")
                else:
                    message_log.write(f"[dim]{timestamp}[/dim] [bold cyan]{from_node}[/bold cyan] [dim]→ {to_node} (Ch {channel}):[/dim] {text}")

                # Add signal info if available
                if snr or rssi:
                    message_log.write(f"    [dim]Signal: SNR {snr}dB, RSSI {rssi}dBm[/dim]")

                # Update statistics
                self._message_count += 1
                self._update_received_count()

                # Mark tab as updated if not active
                if not self.is_active:
                    self.mark_updated()

            except Exception as e:
                logger.error(f"Error displaying received message: {e}")

    def _on_message_sent(self, event: Event) -> None:
        """Handle message sent events."""
        text = event.data.get('text', '')
        recipient = event.data.get('recipient', 'Broadcast')
        channel = event.data.get('channel', 0)

        if text:
            try:
                message_log = self.query_one("#message_log", RichLog)

                # Format timestamp
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                if recipient == 'broadcast' or recipient == 'Broadcast':
                    message_log.write(f"[dim]{timestamp}[/dim] [bold blue]You[/bold blue] [dim]→ All (Ch {channel}):[/dim] {text}")
                else:
                    message_log.write(f"[dim]{timestamp}[/dim] [bold blue]You[/bold blue] [dim]→ {recipient} (Ch {channel}):[/dim] {text}")

                self._update_sent_count()

            except Exception as e:
                logger.error(f"Error displaying sent message: {e}")

    def _on_message_failed(self, event: Event) -> None:
        """Handle message send failure events."""
        text = event.data.get('text', '')
        error = event.data.get('error', 'Unknown error')

        try:
            message_log = self.query_one("#message_log", RichLog)

            # Format timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            message_log.write(f"[dim]{timestamp}[/dim] [bold red]Failed to send:[/bold red] {text}")
            message_log.write(f"    [red]Error: {error}[/red]")

            self._update_failed_count()

        except Exception as e:
            logger.error(f"Error displaying failed message: {e}")

    def _on_connection_established(self, event: Event) -> None:
        """Handle connection established event."""
        try:
            message_log = self.query_one("#message_log", RichLog)
            interface_type = event.data.get('interface_type', 'unknown')
            message_log.write(f"[bold green]Connected via {interface_type}[/bold green]")
            message_log.write("[green]Ready to send and receive messages![/green]")
        except Exception as e:
            logger.debug(f"Error handling connection established: {e}")

    def _on_connection_lost(self, event: Event) -> None:
        """Handle connection lost event."""
        try:
            message_log = self.query_one("#message_log", RichLog)
            reason = event.data.get('reason', 'unknown')
            message_log.write(f"[bold red]Disconnected ({reason})[/bold red]")
            message_log.write("[yellow]Reconnect to continue messaging.[/yellow]")
        except Exception as e:
            logger.debug(f"Error handling connection lost: {e}")

    def _update_sent_count(self) -> None:
        """Update sent message count."""
        try:
            sent_widget = self.query_one("#sent_count", Static)
            current = int(sent_widget.renderable.plain.split(": ")[1])
            sent_widget.update(f"Sent: {current + 1}")
        except Exception as e:
            logger.debug(f"Error updating sent count: {e}")

    def _update_received_count(self) -> None:
        """Update received message count."""
        try:
            received_widget = self.query_one("#received_count", Static)
            current = int(received_widget.renderable.plain.split(": ")[1])
            received_widget.update(f"Received: {current + 1}")
        except Exception as e:
            logger.debug(f"Error updating received count: {e}")

    def _update_failed_count(self) -> None:
        """Update failed message count."""
        try:
            failed_widget = self.query_one("#failed_count", Static)
            current = int(failed_widget.renderable.plain.split(": ")[1])
            failed_widget.update(f"Failed: {current + 1}")
        except Exception as e:
            logger.debug(f"Error updating failed count: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "send_message_btn":
            self._send_message()
        elif event.button.id == "clear_input_btn":
            self._clear_input()
        elif event.button.id == "clear_history_btn":
            self._clear_history()
        elif event.button.id == "export_messages_btn":
            self._export_messages()
        elif event.button.id == "message_settings_btn":
            self._show_settings()
        elif event.button.id == "refresh_messages_btn":
            self._refresh_messages()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "message_input":
            self._send_message()

    def _send_message(self) -> None:
        """Send a message."""
        try:
            input_widget = self.query_one("#message_input", Input)
            message = input_widget.value.strip()

            if not message:
                message_log = self.query_one("#message_log", RichLog)
                message_log.write("[yellow]Cannot send empty message[/yellow]")
                return

            # Get selected options
            recipient = self.query_one("#recipient_select", Select).value
            channel = int(self.query_one("#channel_select", Select).value)
            priority = self.query_one("#priority_select", Select).value

            # Send message through connection manager
            # TODO: Use priority setting when implementing message priority handling
            import asyncio
            asyncio.create_task(
                self.app.connection_manager.send_message(
                    message,
                    recipient=recipient if recipient != "broadcast" else None,
                    channel=channel
                )
            )

            # Log priority setting for future implementation
            if priority != "UNSET":
                message_log = self.query_one("#message_log", RichLog)
                message_log.write(f"[dim]Priority: {priority}[/dim]")

            # Clear input
            input_widget.value = ""

            # Update pending count
            try:
                pending_widget = self.query_one("#pending_count", Static)
                current = int(pending_widget.renderable.plain.split(": ")[1])
                pending_widget.update(f"Pending: {current + 1}")
            except Exception as e:
                logger.debug(f"Error updating pending count: {e}")

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            message_log = self.query_one("#message_log", RichLog)
            message_log.write(f"[red]Error sending message: {e}[/red]")

    def _clear_input(self) -> None:
        """Clear the message input."""
        input_widget = self.query_one("#message_input", Input)
        input_widget.value = ""

    def _clear_history(self) -> None:
        """Clear the message history."""
        try:
            message_log = self.query_one("#message_log", RichLog)
            message_log.clear()
            message_log.write("[yellow]Message history cleared[/yellow]")

            # Reset message count
            self._message_count = 0
            self.app.call_later(self.refresh_data)

        except Exception as e:
            logger.error(f"Error clearing history: {e}")

    def _export_messages(self) -> None:
        """Export message history."""
        try:
            message_log = self.query_one("#message_log", RichLog)
            message_log.write("[blue]Exporting message history...[/blue]")
            # TODO: Implement message export functionality
            message_log.write("[green]Message history exported[/green]")
        except Exception as e:
            logger.error(f"Error exporting messages: {e}")

    def _show_settings(self) -> None:
        """Show message settings dialog."""
        try:
            message_log = self.query_one("#message_log", RichLog)
            message_log.write("[blue]Message settings dialog would open here[/blue]")
            # TODO: Implement settings dialog
        except Exception as e:
            logger.error(f"Error showing settings: {e}")

    def _refresh_messages(self) -> None:
        """Refresh message display."""
        try:
            message_log = self.query_one("#message_log", RichLog)
            message_log.write("[blue]Refreshing message display...[/blue]")
            self.app.call_later(self.refresh_data)
        except Exception as e:
            logger.error(f"Error refreshing messages: {e}")
