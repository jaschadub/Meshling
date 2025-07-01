"""Auto-detection for Meshtastic devices."""

import asyncio
import platform
from typing import List, Optional, Tuple

import serial.tools.list_ports

from meshling.interfaces.base_interface import BaseInterface
from meshling.interfaces.serial_interface import SerialInterface
from meshling.interfaces.tcp_interface import TCPInterface
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class AutoDetector:
    """Auto-detection for Meshtastic devices on serial and TCP."""

    @staticmethod
    async def find_serial_devices() -> List[str]:
        """Find available serial ports that might have Meshtastic devices.

        Returns:
            List of serial port paths
        """
        try:
            ports = []

            # Get all available serial ports
            available_ports = serial.tools.list_ports.comports()

            for port in available_ports:
                # Filter for likely Meshtastic devices
                port_path = port.device

                # Common patterns for Meshtastic devices
                likely_device = False

                # Check VID/PID for known Meshtastic hardware
                if port.vid and port.pid:
                    # ESP32 development boards commonly used
                    esp32_vids = [0x10C4, 0x1A86, 0x0403, 0x067B]  # Common USB-Serial chips
                    if port.vid in esp32_vids:
                        likely_device = True

                # Check device description
                if port.description:
                    desc_lower = port.description.lower()
                    if any(keyword in desc_lower for keyword in
                           ['cp210', 'ch340', 'ftdi', 'usb serial', 'uart']):
                        likely_device = True

                # Platform-specific filtering
                system = platform.system()
                if system == "Linux":
                    if any(pattern in port_path for pattern in ['/dev/ttyUSB', '/dev/ttyACM']):
                        likely_device = True
                elif system == "Darwin":  # macOS
                    if '/dev/tty.usbserial' in port_path or '/dev/tty.SLAB_USBtoUART' in port_path:
                        likely_device = True
                elif system == "Windows":
                    if port_path.startswith('COM'):
                        likely_device = True

                if likely_device:
                    ports.append(port_path)
                    logger.debug(f"Found potential device: {port_path} ({port.description})")

            return ports

        except Exception as e:
            logger.error(f"Error finding serial devices: {e}")
            return []

    @staticmethod
    async def find_tcp_devices(network_range: str = "192.168.1") -> List[Tuple[str, int]]:
        """Find Meshtastic devices on the local network via TCP.

        Args:
            network_range: Network range to scan (e.g., "192.168.1")

        Returns:
            List of (host, port) tuples
        """
        devices = []
        default_port = 4403

        try:
            # Scan common IP addresses
            scan_tasks = []
            for i in range(1, 255):
                host = f"{network_range}.{i}"
                scan_tasks.append(AutoDetector._check_tcp_host(host, default_port))

            # Run scans concurrently with timeout
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, bool) and result:
                    host = f"{network_range}.{i + 1}"
                    devices.append((host, default_port))
                    logger.debug(f"Found TCP device at {host}:{default_port}")

        except Exception as e:
            logger.error(f"Error scanning for TCP devices: {e}")

        return devices

    @staticmethod
    async def _check_tcp_host(host: str, port: int, timeout: float = 1.0) -> bool:
        """Check if a host has a Meshtastic device listening on the given port.

        Args:
            host: Host to check
            port: Port to check
            timeout: Connection timeout in seconds

        Returns:
            True if device found, False otherwise
        """
        try:
            # Try to connect to the port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )

            # Close the connection immediately
            writer.close()
            await writer.wait_closed()

            return True

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
        except Exception:
            return False

    @staticmethod
    async def auto_detect() -> Optional[BaseInterface]:
        """Auto-detect and connect to the first available Meshtastic device.

        Returns:
            Connected interface or None if no device found
        """
        logger.info("Starting auto-detection for Meshtastic devices")

        # Try serial devices first
        serial_ports = await AutoDetector.find_serial_devices()
        for port in serial_ports:
            logger.info(f"Trying serial connection on {port}")
            interface = SerialInterface(port)

            if await interface.connect():
                logger.info(f"Successfully connected via serial: {port}")
                return interface
            else:
                await interface.disconnect()

        # Try TCP devices if no serial device found
        logger.info("No serial devices found, scanning for TCP devices")
        tcp_devices = await AutoDetector.find_tcp_devices()

        for host, port in tcp_devices:
            logger.info(f"Trying TCP connection to {host}:{port}")
            interface = TCPInterface(host, port)

            if await interface.connect():
                logger.info(f"Successfully connected via TCP: {host}:{port}")
                return interface
            else:
                await interface.disconnect()

        logger.warning("No Meshtastic devices found")
        return None

    @staticmethod
    async def list_available_devices() -> dict:
        """List all available devices without connecting.

        Returns:
            Dictionary with serial and TCP device lists
        """
        logger.info("Scanning for available Meshtastic devices")

        # Find devices concurrently
        serial_task = AutoDetector.find_serial_devices()
        tcp_task = AutoDetector.find_tcp_devices()

        serial_devices, tcp_devices = await asyncio.gather(serial_task, tcp_task)

        return {
            'serial': [{'port': port, 'type': 'serial'} for port in serial_devices],
            'tcp': [{'host': host, 'port': port, 'type': 'tcp'}
                   for host, port in tcp_devices]
        }
