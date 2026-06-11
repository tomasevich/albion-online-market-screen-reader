"""Hotkey listener for global keyboard events."""
import logging
import threading
from typing import Callable

import keyboard

logger = logging.getLogger(__name__)


class HotkeyListener:
    """Service for listening to global hotkey presses."""

    def __init__(self, hotkey: str, callback: Callable):
        """
        Initialize the hotkey listener.
        
        Args:
            hotkey: Hotkey combination to listen for (e.g., "printscreen").
            callback: Function to call when hotkey is pressed.
        """
        self._hotkey = hotkey
        self._callback = callback
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start listening for hotkey presses."""
        if self._running:
            logger.warning("Hotkey listener already running")
            return
        
        logger.info(f"Listening for hotkey: {self._hotkey}")
        
        # Register hotkey callback
        keyboard.add_hotkey(
            self._hotkey,
            self._on_hotkey_pressed,
            suppress=False  # Allow the key to pass through
        )
        
        self._running = True
        
        # Start listener thread
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        
        logger.info("Hotkey listener started")

    def stop(self) -> None:
        """Stop listening for hotkey presses."""
        if not self._running:
            return
        
        logger.info("Stopping hotkey listener...")
        self._running = False
        
        # Unregister hotkey
        keyboard.remove_hotkey(self._hotkey)
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        logger.info("Hotkey listener stopped")

    def _on_hotkey_pressed(self) -> None:
        """Handle hotkey press."""
        if not self._running:
            return
        
        try:
            self._callback()
        except Exception as e:
            logger.exception(f"Error in hotkey callback: {e}")

    def _listen_loop(self) -> None:
        """Main loop for listening to keyboard events."""
        while self._running:
            keyboard.wait(0.1)  # Small sleep to prevent busy-waiting
