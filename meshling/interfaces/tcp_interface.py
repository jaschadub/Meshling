"""TCP interface for WiFi Meshtastic device communication."""

import asyncio
from typing import Any, Dict, Optional

import meshtastic.tcp_interface
from meshtastic import mesh_pb2

from meshling.interfaces.base_interface import BaseInterface, ConnectionStatus
from meshling.utils.exceptions import TCPConnectionError
from meshling.utils.logging import get_logger

logger = get_logger(__name__)


class TCPInterface(BaseInterface):
    """TCP interface for Meshtastic devices connected via WiFi."""

    def __init__(self, host: str, port: int = 4403):
        super().__init__()
        self.host = host
        self.port = port
        self._interface: Optional[meshtastic.tcp_interface.TCPInterface] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect to the Meshtastic device via TCP.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._update_status(ConnectionStatus.CONNECTING)
            logger.info(f"Connecting to device at {self.host}:{self.port}")

            # Create TCP interface in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            self._interface = await loop.run_in_executor(
                None,
                lambda: meshtastic.tcp_interface.TCPInterface(
                    hostname=self.host,
                    portNumber=self.port,
                    debugOut=None  # Disable debug output
                )
            )

            if self._interface:
                # Set up packet callback
                self._interface.onReceive = self._on_receive

                # Get device info
                await self._update_device_info()

                # Start monitoring
                self._monitor_task = asyncio.create_task(self._monitor_connection())

                self._update_status(ConnectionStatus.CONNECTED)
                logger.info(f"Successfully connected to device at {self.host}:{self.port}")
                return True
            else:
                raise TCPConnectionError("Failed to create TCP interface")

        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self._update_status(ConnectionStatus.FAILED)
            return False

    async def disconnect(self) -> None:
        """Disconnect from the Meshtastic device."""
        logger.info("Disconnecting from TCP device")

        # Cancel monitoring
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # Close interface
        if self._interface:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._interface.close)
            except Exception as e:
                logger.error(f"Error closing TCP interface: {e}")
            finally:
                self._interface = None

        self._update_status(ConnectionStatus.DISCONNECTED)
        logger.info("Disconnected from TCP device")

    async def send_message(self, text: str, destination: Optional[str] = None) -> bool:
        """Send a text message via TCP interface.

        Args:
            text: Message text to send
            destination: Optional destination node ID

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self._interface or self._status != ConnectionStatus.CONNECTED:
            logger.error("Cannot send message: not connected")
            return False

        try:
            logger.debug(f"Sending message: {text}")

            # Send message in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._interface.sendText(
                    text,
                    destinationId=destination
                )
            )

            logger.debug("Message sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def get_node_info(self) -> Dict[str, Any]:
        """Get information about connected nodes.

        Returns:
            Dictionary containing node information
        """
        if not self._interface:
            return {}

        try:
            loop = asyncio.get_event_loop()
            nodes = await loop.run_in_executor(
                None,
                lambda: getattr(self._interface, 'nodes', {})
            )

            # Convert to serializable format
            node_info = {}
            for node_id, node in nodes.items():
                node_info[str(node_id)] = {
                    'id': str(node_id),
                    'user': getattr(node, 'user', {}),
                    'position': getattr(node, 'position', {}),
                    'lastHeard': getattr(node, 'lastHeard', 0),
                }

            return node_info

        except Exception as e:
            logger.error(f"Failed to get node info: {e}")
            return {}

    def _on_receive(self, packet: mesh_pb2.MeshPacket, interface: Any) -> None:
        """Handle received packet from Meshtastic device.

        Args:
            packet: Received mesh packet
            interface: Interface that received the packet
        """
        try:
            # Convert packet to dictionary for easier handling
            packet_dict = {
                'from': packet.from_,
                'to': packet.to,
                'id': packet.id,
                'rx_time': packet.rx_time,
                'rx_snr': packet.rx_snr,
                'rx_rssi': packet.rx_rssi,
                'hop_limit': packet.hop_limit,
                'decoded': {}
            }

            # Add decoded payload if available
            if hasattr(packet, 'decoded') and packet.decoded:
                decoded = packet.decoded
                packet_dict['decoded'] = {
                    'portnum': decoded.portnum,
                    'payload': decoded.payload,
                }

                # Add text if it's a text message
                if hasattr(decoded, 'text') and decoded.text:
                    packet_dict['decoded']['text'] = decoded.text

            self._handle_packet(packet_dict)

        except Exception as e:
            logger.error(f"Error processing received packet: {e}")

    async def _update_device_info(self) -> None:
        """Update device information."""
        if not self._interface:
            return

        try:
            loop = asyncio.get_event_loop()

            # Get device info in executor
            my_info = await loop.run_in_executor(
                None,
                lambda: getattr(self._interface, 'myInfo', {})
            )

            self._device_info = {
                'host': self.host,
                'port': self.port,
                'type': 'tcp',
                'my_info': my_info,
                'firmware_version': getattr(my_info, 'firmware_version', 'Unknown'),
                'hw_model': getattr(my_info, 'hw_model', 'Unknown'),
            }

        except Exception as e:
            logger.error(f"Failed to update device info: {e}")

    async def _monitor_connection(self) -> None:
        """Monitor connection status and handle reconnection."""
        while self._status == ConnectionStatus.CONNECTED:
            try:
                await asyncio.sleep(5.0)  # Check every 5 seconds

                # Simple check - try to access interface
                if not self._interface:
                    logger.warning("TCP interface lost")
                    self._update_status(ConnectionStatus.FAILED)
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")
                self._update_status(ConnectionStatus.FAILED)
                break
