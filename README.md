# Meshling

Cross-platform terminal user interface for Meshtastic mesh networking devices.

## Features

- **Cross-platform compatibility** - Works on Linux, macOS, and Windows
- **Multiple connection types** - USB/Serial and TCP/WiFi with auto-detection
- **Real-time packet monitoring** - Live display of mesh network traffic
- **Message sending** - Send text messages to the mesh network
- **Device status** - Monitor connection and device information
- **Extensible architecture** - Built for easy feature additions

## Installation

### From PyPI (when available)

```bash
pip install meshling
```

### From Source

```bash
git clone https://github.com/meshling/meshling.git
cd meshling
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/meshling/meshling.git
cd meshling
pip install -e ".[dev]"
```

## Usage

### Basic Usage

```bash
# Auto-detect and connect to device
meshling

# Connect to specific serial port
meshling --port /dev/ttyUSB0

# Connect via TCP/WiFi
meshling --host 192.168.1.100

# Enable debug logging
meshling --debug
```

### Command Line Options

- `--port, -p` - Serial port for USB connection (e.g., `/dev/ttyUSB0`, `COM3`)
- `--host, -h` - Host for TCP connection (e.g., `192.168.1.100`)
- `--tcp-port` - Port for TCP connection (default: 4403)
- `--debug, -d` - Enable debug logging
- `--log-file` - Log file path (default: `meshling.log`)

### Interface

The TUI is divided into several sections:

- **Header** - Shows connection status and current time
- **Packet Log** - Real-time display of mesh network packets and messages
- **Device Status** - Connection status, device type, and firmware version
- **Message Input** - Text field and send button for composing messages
- **Connection Panel** - Auto-connect and disconnect controls
- **Footer** - Application information and key bindings

### Keyboard Shortcuts

- `Ctrl+C` - Exit application
- `Enter` - Send message (when in message input field)
- `Tab` - Navigate between UI elements

## Requirements

- Python 3.8 or higher
- Meshtastic device (connected via USB or WiFi)

### System Requirements

#### Linux
- Access to serial ports (may require adding user to `dialout` group)
- `sudo usermod -a -G dialout $USER` (logout/login required)

#### macOS
- No additional requirements

#### Windows
- USB drivers for your Meshtastic device
- Windows Terminal recommended for best experience

## Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/meshling/meshling.git
cd meshling

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=meshling

# Run linting
ruff check meshling/
bandit -r meshling/
```

### Code Quality

This project uses:
- **ruff** for linting and formatting
- **bandit** for security analysis
- **mypy** for type checking
- **pytest** for testing

## Architecture

Meshling is built with a modular architecture:

- **Core** - Connection management, event bus, packet handling
- **Interfaces** - Serial and TCP communication with Meshtastic devices
- **UI** - Textual-based terminal user interface components
- **Utils** - Logging, exceptions, and utility functions

See [`TECHNICAL_PLAN.md`](TECHNICAL_PLAN.md) for detailed architecture documentation.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && ruff check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Copyright

Copyright (c) 2025 Jascha Wanger / Tarnover, LLC

## Acknowledgments

- [Meshtastic](https://meshtastic.org/) - The mesh networking platform
- [Textual](https://textual.textualize.io/) - The Python TUI framework
- The Meshtastic community for their excellent documentation and support

## Support

- [GitHub Issues](https://github.com/meshling/meshling/issues) - Bug reports and feature requests
- [Meshtastic Discord](https://discord.gg/ktMAKGBnBs) - Community support
- [Documentation](https://github.com/meshling/meshling/wiki) - User guides and tutorials