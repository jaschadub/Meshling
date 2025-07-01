"""Base interface for Meshtastic device communication."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, Optional

from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionStatus(Enum):
    """Connection status enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


class BaseInterface(ABC):
    """Abstract base class for Meshtastic device interfaces."""

    def __init__(self):
        self._status = ConnectionStatus.DISCONNECTED
        self._packet_callback: Optional[Callable] = None
        self._connection_callback: Optional[Callable] = None
        self._device_info: Dict[str, Any] = {}

    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._status

    @property
    def device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return self._device_info.copy()

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the Meshtastic device.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the Meshtastic device."""
        pass

    @abstractmethod
    async def send_message(self, text: str, destination: Optional[str] = None) -> bool:
        """Send a text message.

        Args:
            text: Message text to send
            destination: Optional destination node ID

        Returns:
            True if message sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_node_info(self) -> Dict[str, Any]:
        """Get information about connected nodes.

        Returns:
            Dictionary containing node information
        """
        pass

    def set_packet_callback(self, callback: Callable) -> None:
        """Set callback for received packets.

        Args:
            callback: Function to call when packet is received
        """
        self._packet_callback = callback
        logger.debug("Packet callback set")

    def set_connection_callback(self, callback: Callable) -> None:
        """Set callback for connection status changes.

        Args:
            callback: Function to call when connection status changes
        """
        self._connection_callback = callback
        logger.debug("Connection callback set")

    def _update_status(self, new_status: ConnectionStatus) -> None:
        """Update connection status and notify callback.

        Args:
            new_status: New connection status
        """
        if self._status != new_status:
            old_status = self._status
            self._status = new_status
            logger.debug(f"Status changed: {old_status.value} -> {new_status.value}")

            if self._connection_callback:
                try:
                    self._connection_callback(new_status)
                except Exception as e:
                    logger.error(f"Error in connection callback: {e}")

    def _handle_packet(self, packet: Any) -> None:
        """Handle received packet and notify callback.

        Args:
            packet: Received packet data
        """
        if self._packet_callback:
            try:
                self._packet_callback(packet)
            except Exception as e:
                logger.error(f"Error in packet callback: {e}")
        else:
            logger.debug("Received packet but no callback set")
