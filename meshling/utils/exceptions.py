"""Custom exceptions for Meshling."""


class MeshlingError(Exception):
    """Base exception for all Meshling errors."""
    pass


class ConnectionError(MeshlingError):
    """Raised when connection to Meshtastic device fails."""
    pass


class DeviceNotFoundError(ConnectionError):
    """Raised when no Meshtastic device is found."""
    pass


class SerialConnectionError(ConnectionError):
    """Raised when serial connection fails."""
    pass


class TCPConnectionError(ConnectionError):
    """Raised when TCP connection fails."""
    pass


class PacketError(MeshlingError):
    """Raised when packet processing fails."""
    pass


class ConfigurationError(MeshlingError):
    """Raised when configuration is invalid."""
    pass


class UIError(MeshlingError):
    """Raised when UI operation fails."""
    pass
