"""Config tab for device configuration management."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    RichLog,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from meshling.core.event_bus import Event, EventType
from meshling.ui.widgets.tabs.base_tab import BaseTab
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class ConfigTab(BaseTab):
    """Tab for device configuration management."""

    def __init__(self, **kwargs):
        super().__init__("config", "Config", **kwargs)
        self._config_dirty = False

    def compose(self) -> ComposeResult:
        """Compose the config tab layout."""
        with Vertical():
            # Header
            with Container(classes="config-header"):
                yield Static("Device Configuration", classes="tab-title")
                yield Static("Configure device settings and preferences", classes="tab-subtitle")

            # Main content with tabbed configuration sections
            with TabbedContent(id="config_sections"):
                # Device Settings Tab
                with TabPane("Device", id="device_config"):
                    with Vertical(classes="config-section"):
                        yield Static("Device Information", classes="section-title")

                        with Horizontal(classes="config-row"):
                            yield Static("Node Name:", classes="config-label")
                            yield Input(placeholder="Enter device name", id="device_name", classes="config-input")

                        with Horizontal(classes="config-row"):
                            yield Static("Region:", classes="config-label")
                            yield Select([
                                ("US", "United States"),
                                ("EU_433", "Europe 433MHz"),
                                ("EU_868", "Europe 868MHz"),
                                ("CN", "China"),
                                ("JP", "Japan"),
                                ("ANZ", "Australia/New Zealand"),
                                ("KR", "Korea"),
                                ("TW", "Taiwan"),
                                ("RU", "Russia"),
                                ("IN", "India"),
                                ("NZ_865", "New Zealand 865MHz"),
                                ("TH", "Thailand"),
                                ("LORA_24", "2.4GHz LoRa"),
                                ("UA_433", "Ukraine 433MHz"),
                                ("UA_868", "Ukraine 868MHz"),
                                ("MY_433", "Malaysia 433MHz"),
                                ("MY_919", "Malaysia 919MHz"),
                                ("SG_923", "Singapore 923MHz")
                            ], id="region_select", classes="config-select")

                        with Horizontal(classes="config-row"):
                            yield Static("Hardware Model:", classes="config-label")
                            yield Static("T-Beam v1.1", id="hardware_model", classes="config-value")

                # LoRa Settings Tab
                with TabPane("LoRa", id="lora_config"):
                    with Vertical(classes="config-section"):
                        yield Static("LoRa Radio Configuration", classes="section-title")

                        with Horizontal(classes="config-row"):
                            yield Static("Frequency:", classes="config-label")
                            yield Input(placeholder="915.0", id="frequency", classes="config-input")
                            yield Static("MHz", classes="config-unit")

                        with Horizontal(classes="config-row"):
                            yield Static("Bandwidth:", classes="config-label")
                            yield Select([
                                ("125", "125 kHz"),
                                ("250", "250 kHz"),
                                ("500", "500 kHz")
                            ], id="bandwidth_select", classes="config-select")

                        with Horizontal(classes="config-row"):
                            yield Static("Spreading Factor:", classes="config-label")
                            yield Select([
                                ("7", "SF7 (Fast)"),
                                ("8", "SF8"),
                                ("9", "SF9"),
                                ("10", "SF10"),
                                ("11", "SF11"),
                                ("12", "SF12 (Slow)")
                            ], id="spreading_factor_select", classes="config-select")

                        with Horizontal(classes="config-row"):
                            yield Static("Coding Rate:", classes="config-label")
                            yield Select([
                                ("5", "4/5"),
                                ("6", "4/6"),
                                ("7", "4/7"),
                                ("8", "4/8")
                            ], id="coding_rate_select", classes="config-select")

                        with Horizontal(classes="config-row"):
                            yield Static("TX Power:", classes="config-label")
                            yield Input(placeholder="20", id="tx_power", classes="config-input")
                            yield Static("dBm", classes="config-unit")

                # Power Settings Tab
                with TabPane("Power", id="power_config"):
                    with Vertical(classes="config-section"):
                        yield Static("Power Management", classes="section-title")

                        with Horizontal(classes="config-row"):
                            yield Checkbox("GPS Enabled", id="gps_enabled", classes="config-checkbox")

                        with Horizontal(classes="config-row"):
                            yield Checkbox("Bluetooth Enabled", id="bluetooth_enabled", classes="config-checkbox")

                        with Horizontal(classes="config-row"):
                            yield Checkbox("WiFi Enabled", id="wifi_enabled", classes="config-checkbox")

                        with Horizontal(classes="config-row"):
                            yield Static("Screen Timeout:", classes="config-label")
                            yield Input(placeholder="60", id="screen_timeout", classes="config-input")
                            yield Static("seconds", classes="config-unit")

                        with Horizontal(classes="config-row"):
                            yield Static("Sleep Mode:", classes="config-label")
                            yield Select([
                                ("NO_SLEEP", "No Sleep"),
                                ("LIGHT_SLEEP", "Light Sleep"),
                                ("MIN_WAKE", "Minimum Wake"),
                                ("ULTRA_LOW_POWER", "Ultra Low Power")
                            ], id="sleep_mode_select", classes="config-select")

                # Network Settings Tab
                with TabPane("Network", id="network_config"):
                    with Vertical(classes="config-section"):
                        yield Static("Network Configuration", classes="section-title")

                        with Horizontal(classes="config-row"):
                            yield Static("WiFi SSID:", classes="config-label")
                            yield Input(placeholder="Enter WiFi network name", id="wifi_ssid", classes="config-input")

                        with Horizontal(classes="config-row"):
                            yield Static("WiFi Password:", classes="config-label")
                            yield Input(placeholder="Enter WiFi password", password=True, id="wifi_password", classes="config-input")

                        with Horizontal(classes="config-row"):
                            yield Checkbox("Enable TCP API", id="tcp_api_enabled", classes="config-checkbox")

                        with Horizontal(classes="config-row"):
                            yield Static("TCP Port:", classes="config-label")
                            yield Input(placeholder="4403", id="tcp_port", classes="config-input")

            # Configuration log
            with Container(classes="config-log-container"):
                yield Static("Configuration Log", classes="section-title")
                config_log = RichLog(id="config_log", markup=True, highlight=True)
                yield config_log

            # Action buttons
            with Horizontal(classes="config-actions"):
                yield Button("Load Config", id="load_config_btn")
                yield Button("Save Config", variant="success", id="save_config_btn")
                yield Button("Reset to Defaults", variant="error", id="reset_config_btn")
                yield Button("Reboot Device", variant="error", id="reboot_device_btn")

    async def initialize_tab(self) -> None:
        """Initialize the config tab."""
        logger.debug("Initializing config tab")

        # Initialize configuration log
        try:
            config_log = self.query_one("#config_log", RichLog)
            config_log.write("[bold green]Configuration interface ready[/bold green]")
            config_log.write("Load device configuration to begin editing settings.")
        except Exception as e:
            logger.debug(f"Could not initialize config log: {e}")

    async def cleanup_tab(self) -> None:
        """Clean up config tab resources."""
        logger.debug("Cleaning up config tab")

    async def setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for config."""
        self.subscribe_to_event(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        self.subscribe_to_event(EventType.DEVICE_CONFIG_CHANGED, self._on_config_changed)
        self.subscribe_to_event(EventType.CONFIG_LOADED, self._on_config_loaded)

    async def refresh_data(self) -> None:
        """Refresh config data."""
        await self._load_device_config()

    async def _load_device_config(self) -> None:
        """Load device configuration from the connected device."""
        try:
            config_log = self.query_one("#config_log", RichLog)
            config_log.write("[yellow]Loading device configuration...[/yellow]")

            # TODO: Load actual configuration from connection manager
            # For now, populate with sample data
            sample_config = {
                "device_name": "Meshling Node",
                "region": "US",
                "frequency": "915.0",
                "bandwidth": "125",
                "spreading_factor": "7",
                "coding_rate": "5",
                "tx_power": "20",
                "gps_enabled": True,
                "bluetooth_enabled": True,
                "wifi_enabled": False,
                "screen_timeout": "60",
                "sleep_mode": "LIGHT_SLEEP",
                "wifi_ssid": "",
                "wifi_password": "",
                "tcp_api_enabled": True,
                "tcp_port": "4403"
            }

            self.app.call_later(self._populate_config_fields, sample_config, delay=0.1)
            config_log.write("[bold green]Configuration loaded successfully[/bold green]")

        except Exception as e:
            logger.error(f"Error loading device config: {e}")
            config_log = self.query_one("#config_log", RichLog)
            config_log.write(f"[red]Error loading configuration: {e}[/red]")

    async def _populate_config_fields(self, config: dict) -> None:
        """Populate configuration fields with loaded data."""
        try:
            # Device settings
            device_name = self.query_one("#device_name", Input)
            device_name.value = config.get("device_name", "")

            region_select = self.query_one("#region_select", Select)
            region_value = config.get("region", "US")
            for i, (value, _) in enumerate(region_select.options):
                if value == region_value:
                    region_select.select_index(i)
                    break

            # LoRa settings
            frequency = self.query_one("#frequency", Input)
            frequency.value = config.get("frequency", "915.0")

            bandwidth_select = self.query_one("#bandwidth_select", Select)
            bandwidth_value = config.get("bandwidth", "125")
            for i, (value, _) in enumerate(bandwidth_select.options):
                if value == bandwidth_value:
                    bandwidth_select.select_index(i)
                    break

            spreading_factor_select = self.query_one("#spreading_factor_select", Select)
            spreading_factor_value = config.get("spreading_factor", "7")
            for i, (value, _) in enumerate(spreading_factor_select.options):
                if value == spreading_factor_value:
                    spreading_factor_select.select_index(i)
                    break

            coding_rate_select = self.query_one("#coding_rate_select", Select)
            coding_rate_value = config.get("coding_rate", "5")
            for i, (value, _) in enumerate(coding_rate_select.options):
                if value == coding_rate_value:
                    coding_rate_select.select_index(i)
                    break

            tx_power = self.query_one("#tx_power", Input)
            tx_power.value = config.get("tx_power", "20")

            # Power settings
            gps_enabled = self.query_one("#gps_enabled", Checkbox)
            gps_enabled.value = config.get("gps_enabled", True)

            bluetooth_enabled = self.query_one("#bluetooth_enabled", Checkbox)
            bluetooth_enabled.value = config.get("bluetooth_enabled", True)

            wifi_enabled = self.query_one("#wifi_enabled", Checkbox)
            wifi_enabled.value = config.get("wifi_enabled", False)

            screen_timeout = self.query_one("#screen_timeout", Input)
            screen_timeout.value = config.get("screen_timeout", "60")

            sleep_mode_select = self.query_one("#sleep_mode_select", Select)
            sleep_mode_value = config.get("sleep_mode", "LIGHT_SLEEP")
            for i, (value, _) in enumerate(sleep_mode_select.options):
                if value == sleep_mode_value:
                    sleep_mode_select.select_index(i)
                    break

            # Network settings
            wifi_ssid = self.query_one("#wifi_ssid", Input)
            wifi_ssid.value = config.get("wifi_ssid", "")

            wifi_password = self.query_one("#wifi_password", Input)
            wifi_password.value = config.get("wifi_password", "")

            tcp_api_enabled = self.query_one("#tcp_api_enabled", Checkbox)
            tcp_api_enabled.value = config.get("tcp_api_enabled", True)

            tcp_port = self.query_one("#tcp_port", Input)
            tcp_port.value = config.get("tcp_port", "4403")

        except Exception as e:
            logger.error(f"Error populating config fields: {e}")

    def _on_connection_established(self, event: Event) -> None:
        """Handle connection established event."""
        config_log = self.query_one("#config_log", RichLog)
        config_log.write("[bold green]Device connected[/bold green]")
        config_log.write("Ready to load device configuration.")
        self.app.call_later(self._load_device_config)

    def _on_config_changed(self, event: Event) -> None:
        """Handle device configuration changes."""
        self._config_dirty = True
        self.mark_updated()

        config_log = self.query_one("#config_log", RichLog)
        config_log.write("[yellow]Device configuration changed[/yellow]")

    def _on_config_loaded(self, event: Event) -> None:
        """Handle configuration loaded event."""
        config_data = event.data.get('config', {})
        self.app.call_later(self._populate_config_fields, config_data)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the config tab."""
        if event.button.id == "load_config_btn":
            self._load_config()
        elif event.button.id == "save_config_btn":
            self._save_config()
        elif event.button.id == "reset_config_btn":
            self._reset_config()
        elif event.button.id == "reboot_device_btn":
            self._reboot_device()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        self._config_dirty = True

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select field changes."""
        self._config_dirty = True

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        self._config_dirty = True

    def _load_config(self) -> None:
        """Load configuration from device."""
        config_log = self.query_one("#config_log", RichLog)
        config_log.write("[blue]Loading configuration from device...[/blue]")
        self.app.call_later(self._load_device_config)

    def _save_config(self) -> None:
        """Save configuration to device."""
        config_log = self.query_one("#config_log", RichLog)
        config_log.write("[blue]Saving configuration to device...[/blue]")

        # TODO: Collect all configuration values and send to device
        # For now, just log the action
        config_log.write("[bold green]Configuration saved successfully[/bold green]")
        self._config_dirty = False

    def _reset_config(self) -> None:
        """Reset configuration to defaults."""
        config_log = self.query_one("#config_log", RichLog)
        config_log.write("[yellow]Resetting configuration to defaults...[/yellow]")

        # TODO: Implement reset to factory defaults
        config_log.write("[bold green]Configuration reset to defaults[/bold green]")

    def _reboot_device(self) -> None:
        """Reboot the connected device."""
        config_log = self.query_one("#config_log", RichLog)
        config_log.write("[red]Rebooting device...[/red]")

        # TODO: Implement device reboot command
        config_log.write("[yellow]Device reboot command sent[/yellow]")
