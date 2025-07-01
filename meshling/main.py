"""Main entry point for Meshling TUI application."""

import sys
from typing import Optional

import click

from meshling.app import MeshlingApp
from meshling.utils.logging import setup_logging


@click.command()
@click.option(
    "--port",
    "-p",
    help="Serial port for USB connection (e.g., /dev/ttyUSB0, COM3)",
    type=str,
)
@click.option(
    "--host",
    "-h",
    help="Host for TCP connection (e.g., 192.168.1.100)",
    type=str,
)
@click.option(
    "--tcp-port",
    help="Port for TCP connection (default: 4403)",
    type=int,
    default=4403,
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug logging",
)
@click.option(
    "--log-file",
    help="Log file path (default: meshling.log)",
    type=str,
    default="meshling.log",
)
@click.version_option(version="0.1.0", prog_name="meshling")
def main(
    port: Optional[str],
    host: Optional[str],
    tcp_port: int,
    debug: bool,
    log_file: str,
) -> None:
    """Meshling - Cross-platform TUI for Meshtastic devices.

    Launch the terminal user interface for interacting with Meshtastic mesh
    networking devices. Supports both USB/serial and TCP/WiFi connections
    with automatic device detection.

    Examples:
        meshling                    # Auto-detect connection
        meshling -p /dev/ttyUSB0    # Use specific serial port
        meshling -h 192.168.1.100   # Connect via TCP/WiFi
    """
    # Setup logging
    setup_logging(debug=debug, log_file=log_file)

    # Validate connection options
    if port and host:
        click.echo("Error: Cannot specify both --port and --host", err=True)
        sys.exit(1)

    # Create and run the application
    app = MeshlingApp(
        serial_port=port,
        tcp_host=host,
        tcp_port=tcp_port,
    )

    try:
        app.run()
    except KeyboardInterrupt:
        click.echo("\nShutting down Meshling...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
