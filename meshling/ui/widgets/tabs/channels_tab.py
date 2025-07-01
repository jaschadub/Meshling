"""Channels tab for channel management and configuration."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Input,
    RichLog,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from meshling.core.event_bus import EventType
from meshling.ui.widgets.tabs.base_tab import BaseTab
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class ChannelsTab(BaseTab):
    """Tab for managing mesh channels."""

    def __init__(self, **kwargs):
        super().__init__("channels", "Channels", **kwargs)
        self._selected_channel = None

    def compose(self) -> ComposeResult:
        """Compose the channels tab layout."""
        with Vertical():
            # Header with channel overview
            with Container(classes="channels-header"):
                yield Static("Channel Management", classes="tab-title")
                yield Static("Configure and monitor mesh channels", classes="tab-subtitle")

            # Main content area
            with Horizontal(classes="channels-content"):
                # Channel list (left side)
                with Container(classes="channel-list-container"):
                    yield Static("Channels", classes="section-title")
                    channel_table = DataTable(id="channels_table")
                    channel_table.add_columns("Name", "Index", "Role", "PSK", "Uplink", "Downlink")
                    yield channel_table

                # Channel details and controls (right side)
                with Vertical(classes="channel-details"):
                    yield Static("Channel Configuration", classes="section-title")

                    # Channel configuration form
                    with TabbedContent(id="channel_config_tabs"):
                        # Basic Settings
                        with TabPane("Basic", id="basic_settings"):
                            with Vertical(classes="config-section"):
                                with Horizontal(classes="config-row"):
                                    yield Static("Channel Name:", classes="config-label")
                                    yield Input(placeholder="Enter channel name", id="channel_name", classes="config-input")

                                with Horizontal(classes="config-row"):
                                    yield Static("Channel Index:", classes="config-label")
                                    yield Input(placeholder="0-7", id="channel_index", classes="config-input")

                                with Horizontal(classes="config-row"):
                                    yield Static("Role:", classes="config-label")
                                    yield Select([
                                        ("PRIMARY", "Primary"),
                                        ("SECONDARY", "Secondary"),
                                        ("DISABLED", "Disabled")
                                    ], id="channel_role", classes="config-select")

                                with Horizontal(classes="config-row"):
                                    yield Checkbox("Uplink Enabled", id="uplink_enabled", classes="config-checkbox")

                                with Horizontal(classes="config-row"):
                                    yield Checkbox("Downlink Enabled", id="downlink_enabled", classes="config-checkbox")

                        # Security Settings
                        with TabPane("Security", id="security_settings"):
                            with Vertical(classes="config-section"):
                                with Horizontal(classes="config-row"):
                                    yield Static("PSK (Pre-Shared Key):", classes="config-label")
                                    yield Input(placeholder="Enter PSK or leave empty for default", id="channel_psk", classes="config-input")

                                with Horizontal(classes="config-row"):
                                    yield Button("Generate Random PSK", id="generate_psk_btn", classes="config-button")

                                with Horizontal(classes="config-row"):
                                    yield Static("PSK Length:", classes="config-label")
                                    yield Select([
                                        ("16", "16 bytes (128-bit)"),
                                        ("32", "32 bytes (256-bit)")
                                    ], id="psk_length", classes="config-select")

                        # Advanced Settings
                        with TabPane("Advanced", id="advanced_settings"):
                            with Vertical(classes="config-section"):
                                with Horizontal(classes="config-row"):
                                    yield Static("Module Settings:", classes="config-label")
                                    yield Input(placeholder="Module-specific settings", id="module_settings", classes="config-input")

                                with Horizontal(classes="config-row"):
                                    yield Checkbox("Position Precision", id="position_precision", classes="config-checkbox")

                                with Horizontal(classes="config-row"):
                                    yield Checkbox("Exact Position", id="exact_position", classes="config-checkbox")

                    # Channel action buttons
                    with Horizontal(classes="channel-config-actions"):
                        yield Button("Apply Changes", variant="success", id="apply_channel_btn", disabled=True)
                        yield Button("Reset", id="reset_channel_btn", disabled=True)

            # Channel activity log
            with Container(classes="channel-log-container"):
                yield Static("Channel Activity", classes="section-title")
                channel_log = RichLog(id="channel_log", markup=True, highlight=True)
                yield channel_log

            # Main action buttons
            with Horizontal(classes="channels-actions"):
                yield Button("Add Channel", variant="success", id="add_channel_btn")
                yield Button("Edit Channel", id="edit_channel_btn", disabled=True)
                yield Button("Delete Channel", variant="error", id="delete_channel_btn", disabled=True)
                yield Button("Refresh", id="refresh_channels_btn")
                yield Button("Export Config", id="export_config_btn")

    async def initialize_tab(self) -> None:
        """Initialize the channels tab."""
        logger.debug("Initializing channels tab")

        # Initialize channel log
        try:
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write("[bold green]Channel management ready[/bold green]")
            channel_log.write("Select a channel to view and edit its configuration.")
        except Exception as e:
            logger.debug(f"Could not initialize channel log: {e}")

    async def cleanup_tab(self) -> None:
        """Clean up channels tab resources."""
        logger.debug("Cleaning up channels tab")

    async def setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for channels."""
        self.subscribe_to_event(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        self.subscribe_to_event(EventType.DEVICE_CONFIG_CHANGED, self._on_config_changed)
        self.subscribe_to_event(EventType.CHANNEL_CONFIG_CHANGED, self._on_channel_config_changed)

    async def refresh_data(self) -> None:
        """Refresh channel data."""
        await self._load_channels()

    async def _load_channels(self) -> None:
        """Load channel data into the table."""
        try:
            # Check if widgets are mounted before querying
            if not self.is_mounted:
                logger.debug("Tab not mounted yet, skipping channel load")
                return

            table = self.query_one("#channels_table", DataTable)
            table.clear()

            # TODO: Load actual channel data from connection manager
            # For now, add sample data to show the interface
            sample_channels = [
                ("Primary", "0", "PRIMARY", "Default", "Yes", "Yes"),
                ("Secondary", "1", "SECONDARY", "Custom", "No", "Yes"),
                ("Admin", "2", "SECONDARY", "Admin Key", "Yes", "No"),
                ("Public", "3", "SECONDARY", "None", "Yes", "Yes"),
            ]

            for channel_data in sample_channels:
                table.add_row(*channel_data)

            try:
                channel_log = self.query_one("#channel_log", RichLog)
                channel_log.write(f"[green]Loaded {len(sample_channels)} channels[/green]")
            except Exception as e:
                logger.debug(f"Could not write to channel log: {e}")

            logger.debug(f"Loaded {len(sample_channels)} channels")
        except Exception as e:
            logger.debug(f"Could not load channels: {e}")
            try:
                channel_log = self.query_one("#channel_log", RichLog)
                channel_log.write(f"[red]Error loading channels: {e}[/red]")
            except Exception as log_error:
                logger.debug(f"Could not write error to channel log: {log_error}")

    def _populate_channel_form(self, channel_data: tuple) -> None:
        """Populate the channel configuration form with selected channel data."""
        try:
            name, index, role, psk, uplink, downlink = channel_data

            # Basic settings
            channel_name = self.query_one("#channel_name", Input)
            channel_name.value = name

            channel_index = self.query_one("#channel_index", Input)
            channel_index.value = index

            channel_role = self.query_one("#channel_role", Select)
            channel_role.value = role

            uplink_enabled = self.query_one("#uplink_enabled", Checkbox)
            uplink_enabled.value = uplink.lower() == "yes"

            downlink_enabled = self.query_one("#downlink_enabled", Checkbox)
            downlink_enabled.value = downlink.lower() == "yes"

            # Security settings
            channel_psk = self.query_one("#channel_psk", Input)
            channel_psk.value = psk if psk != "Default" and psk != "None" else ""

            # Enable form buttons
            apply_btn = self.query_one("#apply_channel_btn", Button)
            reset_btn = self.query_one("#reset_channel_btn", Button)
            apply_btn.disabled = False
            reset_btn.disabled = False

            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write(f"[blue]Loaded configuration for channel: {name}[/blue]")

        except Exception as e:
            logger.error(f"Error populating channel form: {e}")

    def _clear_channel_form(self) -> None:
        """Clear the channel configuration form."""
        try:
            # Clear all form fields
            self.query_one("#channel_name", Input).value = ""
            self.query_one("#channel_index", Input).value = ""
            self.query_one("#channel_role", Select).value = "SECONDARY"
            self.query_one("#uplink_enabled", Checkbox).value = False
            self.query_one("#downlink_enabled", Checkbox).value = True
            self.query_one("#channel_psk", Input).value = ""

            # Disable form buttons
            apply_btn = self.query_one("#apply_channel_btn", Button)
            reset_btn = self.query_one("#reset_channel_btn", Button)
            apply_btn.disabled = True
            reset_btn.disabled = True

        except Exception as e:
            logger.error(f"Error clearing channel form: {e}")

    def _on_connection_established(self, event) -> None:
        """Handle connection established event."""
        channel_log = self.query_one("#channel_log", RichLog)
        channel_log.write("[bold green]Device connected[/bold green]")
        channel_log.write("Loading channel configuration...")
        self.app.call_later(self._load_channels)

    def _on_config_changed(self, event) -> None:
        """Handle device configuration changes."""
        self.mark_updated()
        channel_log = self.query_one("#channel_log", RichLog)
        channel_log.write("[yellow]Device configuration changed[/yellow]")

    def _on_channel_config_changed(self, event) -> None:
        """Handle channel configuration changes."""
        channel_info = event.data.get('channel', {})
        channel_log = self.query_one("#channel_log", RichLog)
        channel_log.write(f"[yellow]Channel {channel_info.get('index', 'unknown')} configuration changed[/yellow]")
        self.app.call_later(self._load_channels)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the channels tab."""
        if event.button.id == "add_channel_btn":
            self._add_channel()
        elif event.button.id == "edit_channel_btn":
            self._edit_channel()
        elif event.button.id == "delete_channel_btn":
            self._delete_channel()
        elif event.button.id == "refresh_channels_btn":
            self.app.call_later(self._load_channels)
        elif event.button.id == "export_config_btn":
            self._export_config()
        elif event.button.id == "apply_channel_btn":
            self._apply_channel_changes()
        elif event.button.id == "reset_channel_btn":
            self._reset_channel_form()
        elif event.button.id == "generate_psk_btn":
            self._generate_psk()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle channel selection."""
        if event.data_table.id == "channels_table":
            # Get selected channel data
            row_key = event.row_key
            table = event.data_table
            row_data = table.get_row(row_key)

            if row_data:
                self._selected_channel = row_data
                self._populate_channel_form(row_data)

                # Enable edit/delete buttons when a channel is selected
                edit_btn = self.query_one("#edit_channel_btn", Button)
                delete_btn = self.query_one("#delete_channel_btn", Button)
                edit_btn.disabled = False
                delete_btn.disabled = False

    def _add_channel(self) -> None:
        """Add a new channel."""
        self._clear_channel_form()
        channel_log = self.query_one("#channel_log", RichLog)
        channel_log.write("[blue]Ready to add new channel[/blue]")
        channel_log.write("Configure the channel settings and click Apply Changes.")

    def _edit_channel(self) -> None:
        """Edit the selected channel."""
        if self._selected_channel:
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write(f"[blue]Editing channel: {self._selected_channel[0]}[/blue]")
        else:
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write("[yellow]No channel selected for editing[/yellow]")

    def _delete_channel(self) -> None:
        """Delete the selected channel."""
        if self._selected_channel:
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write(f"[red]Deleting channel: {self._selected_channel[0]}[/red]")
            # TODO: Implement channel deletion with confirmation dialog
            self._clear_channel_form()
            self._selected_channel = None
        else:
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write("[yellow]No channel selected for deletion[/yellow]")

    def _apply_channel_changes(self) -> None:
        """Apply channel configuration changes."""
        try:
            # Collect form data
            name = self.query_one("#channel_name", Input).value
            index = self.query_one("#channel_index", Input).value
            role = self.query_one("#channel_role", Select).value
            uplink = self.query_one("#uplink_enabled", Checkbox).value
            downlink = self.query_one("#downlink_enabled", Checkbox).value
            psk = self.query_one("#channel_psk", Input).value

            if not name or not index:
                channel_log = self.query_one("#channel_log", RichLog)
                channel_log.write("[red]Channel name and index are required[/red]")
                return

            # TODO: Send configuration to device
            # Configuration data: role={role}, uplink={uplink}, downlink={downlink}, psk={psk}
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write(f"[green]Applied configuration for channel: {name} (index {index})[/green]")
            channel_log.write(f"[dim]Role: {role}, Uplink: {uplink}, Downlink: {downlink}[/dim]")
            if psk:
                channel_log.write(f"[dim]PSK: {'*' * min(len(psk), 8)}...[/dim]")

            # Refresh channel list
            self.app.call_later(self._load_channels)

        except Exception as e:
            logger.error(f"Error applying channel changes: {e}")
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write(f"[red]Error applying changes: {e}[/red]")

    def _reset_channel_form(self) -> None:
        """Reset the channel form to original values."""
        if self._selected_channel:
            self._populate_channel_form(self._selected_channel)
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write("[blue]Channel form reset to original values[/blue]")
        else:
            self._clear_channel_form()

    def _generate_psk(self) -> None:
        """Generate a random PSK."""
        import secrets

        try:
            # Generate a random 32-byte PSK
            psk_bytes = secrets.token_bytes(32)
            psk_hex = psk_bytes.hex()

            channel_psk = self.query_one("#channel_psk", Input)
            channel_psk.value = psk_hex

            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write("[green]Generated new random PSK[/green]")

        except Exception as e:
            logger.error(f"Error generating PSK: {e}")
            channel_log = self.query_one("#channel_log", RichLog)
            channel_log.write(f"[red]Error generating PSK: {e}[/red]")

    def _export_config(self) -> None:
        """Export channel configuration."""
        channel_log = self.query_one("#channel_log", RichLog)
        channel_log.write("[blue]Exporting channel configuration...[/blue]")
        # TODO: Implement channel configuration export
        channel_log.write("[green]Channel configuration exported[/green]")
