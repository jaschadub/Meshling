"""Nodes tab for mesh network node management."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, RichLog, Static

from meshling.core.event_bus import Event, EventType
from meshling.ui.widgets.tabs.base_tab import BaseTab
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class NodesTab(BaseTab):
    """Tab for managing mesh network nodes."""

    def __init__(self, **kwargs):
        super().__init__("nodes", "Nodes", **kwargs)
        self._node_count = 0

    def compose(self) -> ComposeResult:
        """Compose the nodes tab layout."""
        with Vertical():
            # Header with node overview
            with Container(classes="nodes-header"):
                yield Static("Node Management", classes="tab-title")
                yield Static("Monitor and manage mesh network nodes", classes="tab-subtitle")
                yield Static("Nodes: 0", id="node_count", classes="node-stats")

            # Main content area
            with Horizontal(classes="nodes-content"):
                # Node list (left side)
                with Container(classes="node-list-container"):
                    yield Static("Network Nodes", classes="section-title")
                    node_table = DataTable(id="nodes_table")
                    node_table.add_columns("Node ID", "Short Name", "Long Name", "Hardware", "Role", "Last Seen", "SNR", "Battery")
                    yield node_table

                # Node details (right side)
                with Vertical(classes="node-details"):
                    yield Static("Node Details", classes="section-title")

                    # Node info display
                    with Container(classes="node-info"):
                        yield Static("Select a node to view details", id="node_info_display")

                    # Node activity log
                    yield Static("Node Activity", classes="section-title")
                    node_log = RichLog(id="node_activity_log", markup=True, highlight=True)
                    yield node_log

            # Action buttons
            with Horizontal(classes="nodes-actions"):
                yield Button("Refresh Nodes", id="refresh_nodes_btn")
                yield Button("Request Node Info", id="request_info_btn", disabled=True)
                yield Button("Reboot Node", variant="error", id="reboot_node_btn", disabled=True)
                yield Button("Export Node List", id="export_nodes_btn")

    async def initialize_tab(self) -> None:
        """Initialize the nodes tab."""
        logger.debug("Initializing nodes tab")

        # Initialize activity log
        try:
            node_log = self.query_one("#node_activity_log", RichLog)
            node_log.write("[bold green]Node monitoring started[/bold green]")
            node_log.write("Nodes will appear here as they are discovered on the mesh network.")
        except Exception as e:
            logger.debug(f"Could not initialize node log: {e}")

    async def cleanup_tab(self) -> None:
        """Clean up nodes tab resources."""
        logger.debug("Cleaning up nodes tab")

    async def setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for nodes."""
        self.subscribe_to_event(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        self.subscribe_to_event(EventType.PACKET_RECEIVED, self._on_packet_received)
        self.subscribe_to_event(EventType.NODE_DISCOVERED, self._on_node_discovered)
        self.subscribe_to_event(EventType.NODE_UPDATED, self._on_node_updated)

    async def refresh_data(self) -> None:
        """Refresh node data."""
        await self._load_nodes()

    async def _load_nodes(self) -> None:
        """Load node data into the table."""
        try:
            table = self.query_one("#nodes_table", DataTable)
            table.clear()

            # TODO: Load actual node data from connection manager
            # For now, add sample data to show the interface
            sample_nodes = [
                ("!12345678", "Node1", "Primary Gateway", "T-Beam", "Router", "2 min ago", "8.5 dB", "85%"),
                ("!87654321", "Node2", "Remote Sensor", "Heltec V3", "Client", "5 min ago", "3.2 dB", "72%"),
                ("!11223344", "Node3", "Repeater Alpha", "RAK4631", "Repeater", "1 min ago", "12.1 dB", "N/A"),
            ]

            for node_data in sample_nodes:
                table.add_row(*node_data)

            # Update node count
            self._node_count = len(sample_nodes)
            count_widget = self.query_one("#node_count", Static)
            count_widget.update(f"Nodes: {self._node_count}")

            logger.debug(f"Loaded {len(sample_nodes)} nodes")
        except Exception as e:
            logger.debug(f"Could not load nodes: {e}")

    def _on_connection_established(self, event: Event) -> None:
        """Handle connection established event."""
        node_log = self.query_one("#node_activity_log", RichLog)
        node_log.write("[bold green]Connected to mesh network[/bold green]")
        node_log.write("Scanning for nodes...")
        self.app.call_later(self._load_nodes)

    def _on_packet_received(self, event: Event) -> None:
        """Handle received packet events."""
        packet = event.data.get('packet', {})
        from_node = packet.get('from', 'Unknown')

        # Log node activity
        try:
            node_log = self.query_one("#node_activity_log", RichLog)
            decoded = packet.get('decoded', {})

            if 'text' in decoded:
                node_log.write(f"[cyan]Message from {from_node}:[/cyan] {decoded['text']}")
            else:
                portnum = decoded.get('portnum', 'Unknown')
                node_log.write(f"[dim]Packet from {from_node} ({portnum})[/dim]")
        except Exception as e:
            logger.debug(f"Error logging node activity: {e}")

    def _on_node_discovered(self, event: Event) -> None:
        """Handle node discovery events."""
        node_info = event.data.get('node', {})
        node_id = node_info.get('id', 'Unknown')

        try:
            node_log = self.query_one("#node_activity_log", RichLog)
            node_log.write(f"[bold green]New node discovered:[/bold green] {node_id}")

            # Refresh the node list
            self.app.call_later(self._load_nodes)
        except Exception as e:
            logger.debug(f"Error handling node discovery: {e}")

    def _on_node_updated(self, event: Event) -> None:
        """Handle node update events."""
        node_info = event.data.get('node', {})
        node_id = node_info.get('id', 'Unknown')

        try:
            node_log = self.query_one("#node_activity_log", RichLog)
            node_log.write(f"[yellow]Node updated:[/yellow] {node_id}")

            # Refresh the node list
            self.app.call_later(self._load_nodes)
        except Exception as e:
            logger.debug(f"Error handling node update: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the nodes tab."""
        if event.button.id == "refresh_nodes_btn":
            self.app.call_later(self._load_nodes)
        elif event.button.id == "request_info_btn":
            self._request_node_info()
        elif event.button.id == "reboot_node_btn":
            self._reboot_node()
        elif event.button.id == "export_nodes_btn":
            self._export_nodes()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle node selection."""
        if event.data_table.id == "nodes_table":
            # Get selected node data
            row_key = event.row_key
            table = event.data_table
            row_data = table.get_row(row_key)

            if row_data:
                # Update node info display
                node_id, short_name, long_name, hardware, role, last_seen, snr, battery = row_data

                info_text = f"""[bold]Node ID:[/bold] {node_id}
[bold]Short Name:[/bold] {short_name}
[bold]Long Name:[/bold] {long_name}
[bold]Hardware:[/bold] {hardware}
[bold]Role:[/bold] {role}
[bold]Last Seen:[/bold] {last_seen}
[bold]Signal (SNR):[/bold] {snr}
[bold]Battery:[/bold] {battery}"""

                info_display = self.query_one("#node_info_display", Static)
                info_display.update(info_text)

                # Enable action buttons
                request_btn = self.query_one("#request_info_btn", Button)
                reboot_btn = self.query_one("#reboot_node_btn", Button)
                request_btn.disabled = False
                reboot_btn.disabled = False

    def _request_node_info(self) -> None:
        """Request information from selected node."""
        # TODO: Implement node info request
        node_log = self.query_one("#node_activity_log", RichLog)
        node_log.write("[yellow]Requesting node information...[/yellow]")
        logger.info("Node info request initiated")

    def _reboot_node(self) -> None:
        """Reboot the selected node."""
        # TODO: Implement node reboot with confirmation dialog
        node_log = self.query_one("#node_activity_log", RichLog)
        node_log.write("[red]Node reboot requested[/red]")
        logger.info("Node reboot requested")

    def _export_nodes(self) -> None:
        """Export the node list."""
        # TODO: Implement node list export functionality
        node_log = self.query_one("#node_activity_log", RichLog)
        node_log.write("[blue]Exporting node list...[/blue]")
        logger.info("Node list export requested")
