"""
Communication Module - Hardware interface and serial communication.

This module handles serial communication with the ESP32-based potentiostat,
including connection management, command transmission, and data reception.
"""

from .serial_manager import SerialManager

__all__ = ['SerialManager']
