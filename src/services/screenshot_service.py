"""Service for capturing screenshots."""
import logging
from datetime import datetime
from pathlib import Path

import mss

from src.config import config

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Service responsible for capturing screenshots."""

    def __init__(self):
        """Initialize the screenshot service."""
        self._screenshot_counter = 0

    def capture(self) -> Path:
        """
        Capture a screenshot of the primary monitor.
        
        Returns:
            Path to the saved screenshot file.
        """
        # Generate filename
        timestamp = datetime.now()
        filename = timestamp.strftime(config.SCREENSHOT_FORMAT)
        filepath = config.SCREENSHOTS_DIR / filename
        
        # Capture screen using mss (fast and efficient)
        with mss.mss() as sct:
            # Get primary monitor
            monitor = sct.monitors[1]  # monitors[0] is all monitors
            
            # Capture and save
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
        
        self._screenshot_counter += 1
        logger.info(f"Screenshot #{self._screenshot_counter} captured: {filepath}")
        
        return filepath
