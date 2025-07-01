"""Connection manager for Meshtastic device interfaces."""

import asyncio
from typing import Any, Dict, Optional

from meshling.core.event_bus import EventType, event_bus
from meshling.interfaces.auto_detector import AutoDetector
from meshling.interfaces.base_interface import BaseInterface, ConnectionStatus
from meshling.interfaces.serial_interface import SerialInterface
from meshling.interfaces.tcp_interface import TCPInterface
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages Meshtastic device connections with auto-detection."""

    def __init__(self):
        self._interface: Optional[BaseInterface] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._auto_reconnect = True
        self._connection_params: Optional[Dict[str, Any]] = None

    @property
    def interface(self) -> Optional[BaseInterface]:
        """Get current interface."""
        return self._interface

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return (self._interface is not None and
                self._interface.status == ConnectionStatus.CONNECTED)

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get current connection status."""
        if self._interface:
            return self._interface.status
        return ConnectionStatus.DISCONNECTED

    async def auto_connect(self) -> bool:
        """Auto-detect and connect to the first available device.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Starting auto-connection")

            interface = await AutoDetector.auto_detect()
            if interface:
                await self._set_interface(interface)
                self._connection_params = {'type': 'auto'}

                await event_bus.emit(EventType.CONNECTION_ESTABLISHED, {
                    'interface_type': interface.device_info.get('type', 'unknown'),
                    'device_info': interface.device_info
                })

                return True
            else:
                await event_bus.emit(EventType.CONNECTION_FAILED, {
                    'error': 'No devices found'
                })
                return False

        except Exception as e:
            logger.error(f"Auto-connection failed: {e}")
            await event_bus.emit(EventType.CONNECTION_FAILED, {
                'error': str(e)
            })
            return False

    async def connect_serial(self, port: str) -> bool:
        """Connect to a specific serial port.

        Args:
            port: Serial port path

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to serial port: {port}")

            interface = SerialInterface(port)
            if await interface.connect():
                await self._set_interface(interface)
                self._connection_params = {'type': 'serial', 'port': port}

                await event_bus.emit(EventType.CONNECTION_ESTABLISHED, {
                    'interface_type': 'serial',
                    'port': port,
                    'device_info': interface.device_info
                })

                return True
            else:
                await event_bus.emit(EventType.CONNECTION_FAILED, {
                    'error': f'Failed to connect to {port}'
                })
                return False

        except Exception as e:
            logger.error(f"Serial connection failed: {e}")
            await event_bus.emit(EventType.CONNECTION_FAILED, {
                'error': str(e)
            })
            return False

    async def connect_tcp(self, host: str, port: int = 4403) -> bool:
        """Connect to a TCP host.

        Args:
            host: TCP host address
            port: TCP port number

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to TCP: {host}:{port}")

            interface = TCPInterface(host, port)
            if await interface.connect():
                await self._set_interface(interface)
                self._connection_params = {'type': 'tcp', 'host': host, 'port': port}

                await event_bus.emit(EventType.CONNECTION_ESTABLISHED, {
                    'interface_type': 'tcp',
                    'host': host,
                    'port': port,
                    'device_info': interface.device_info
                })

                return True
            else:
                await event_bus.emit(EventType.CONNECTION_FAILED, {
                    'error': f'Failed to connect to {host}:{port}'
                })
                return False

        except Exception as e:
            logger.error(f"TCP connection failed: {e}")
            await event_bus.emit(EventType.CONNECTION_FAILED, {
                'error': str(e)
            })
            return False

    async def disconnect(self) -> None:
        """Disconnect from current device."""
        logger.info("Disconnecting from device")

        # Cancel reconnection attempts
        self._auto_reconnect = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        # Disconnect interface
        if self._interface:
            await self._interface.disconnect()
            self._interface = None

        self._connection_params = None

        await event_bus.emit(EventType.CONNECTION_LOST, {
            'reason': 'user_requested'
        })

    async def send_message(self, text: str, destination: Optional[str] = None) -> bool:
        """Send a message through the current interface.

        Args:
            text: Message text
            destination: Optional destination node ID

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.is_connected:
            logger.error("Cannot send message: not connected")
            await event_bus.emit(EventType.PACKET_FAILED, {
                'error': 'Not connected'
            })
            return False

        try:
            success = await self._interface.send_message(text, destination)

            if success:
                await event_bus.emit(EventType.PACKET_SENT, {
                    'text': text,
                    'destination': destination
                })
            else:
                await event_bus.emit(EventType.PACKET_FAILED, {
                    'error': 'Send failed'
                })

            return success

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            await event_bus.emit(EventType.PACKET_FAILED, {
                'error': str(e)
            })
            return False

    async def get_device_info(self) -> Dict[str, Any]:
        """Get current device information.

        Returns:
            Device information dictionary
        """
        if self._interface:
            return self._interface.device_info
        return {}

    async def get_node_info(self) -> Dict[str, Any]:
        """Get information about mesh nodes.

        Returns:
            Node information dictionary
        """
        if self.is_connected:
            return await self._interface.get_node_info()
        return {}

    def set_auto_reconnect(self, enabled: bool) -> None:
        """Enable or disable automatic reconnection.

        Args:
            enabled: Whether to enable auto-reconnect
        """
        self._auto_reconnect = enabled
        logger.debug(f"Auto-reconnect {'enabled' if enabled else 'disabled'}")

    async def _set_interface(self, interface: BaseInterface) -> None:
        """Set the current interface and configure callbacks.

        Args:
            interface: Interface to set as current
        """
        # Disconnect existing interface
        if self._interface:
            await self._interface.disconnect()

        self._interface = interface

        # Set up callbacks
        interface.set_packet_callback(self._on_packet_received)
        interface.set_connection_callback(self._on_connection_status_changed)

        logger.debug("Interface set and callbacks configured")

    async def _on_packet_received(self, packet: Dict[str, Any]) -> None:
        """Handle received packet from interface.

        Args:
            packet: Received packet data
        """
        await event_bus.emit(EventType.PACKET_RECEIVED, {
            'packet': packet
        })

    async def _on_connection_status_changed(self, status: ConnectionStatus) -> None:
        """Handle connection status changes.

        Args:
            status: New connection status
        """
        logger.debug(f"Connection status changed: {status.value}")

        if status == ConnectionStatus.FAILED and self._auto_reconnect:
            # Start reconnection attempt
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._attempt_reconnect())

        # Log the device info when connected
        if status == ConnectionStatus.CONNECTED and self._interface:
            logger.info(f"Device info from interface: {self._interface.device_info}")

        # Emit status change event
        await event_bus.emit(EventType.DEVICE_STATUS_CHANGED, {
            'status': status.value,
            'device_info': self._interface.device_info if self._interface else {}
        })

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect using the last connection parameters."""
        if not self._connection_params or not self._auto_reconnect:
            return

        logger.info("Attempting to reconnect...")

        # Wait before reconnecting
        await asyncio.sleep(5.0)

        try:
            params = self._connection_params

            if params['type'] == 'serial':
                await self.connect_serial(params['port'])
            elif params['type'] == 'tcp':
                await self.connect_tcp(params['host'], params['port'])
            elif params['type'] == 'auto':
                await self.auto_connect()

        except Exception as e:
            logger.error(f"Reconnection failed: {e}")

            # Try again after a longer delay
            if self._auto_reconnect:
                await asyncio.sleep(10.0)
                if self._auto_reconnect:  # Check again in case it was disabled
                    self._reconnect_task = asyncio.create_task(self._attempt_reconnect())
