"""Main entry point for the application."""
import logging
import signal
import sys
from pathlib import Path

from src.config import config
from src.services.screenshot_service import ScreenshotService
from src.services.image_analysis_service import ImageAnalysisService
from src.services.data_storage_service import DataStorageService
from src.utils.hotkey_listener import HotkeyListener

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class ScreenMarketScraper:
    """Main application class."""

    def __init__(self):
        """Initialize the application."""
        self._ensure_directories()
        
        self.screenshot_service = ScreenshotService()
        self.analysis_service = ImageAnalysisService()
        self.storage_service = DataStorageService()
        self.hotkey_listener = HotkeyListener(
            hotkey=config.HOTKEY,
            callback=self._on_screenshot_triggered
        )
        self._running = False

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Screenshots directory: {config.SCREENSHOTS_DIR}")
        logger.info(f"Data file: {config.DATA_FILE}")

    def _on_screenshot_triggered(self) -> None:
        """Handle screenshot hotkey press."""
        logger.info("Screenshot triggered!")
        
        try:
            # Step 1: Capture screenshot
            screenshot_path = self.screenshot_service.capture()
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            # Step 2: Analyze image
            result = self.analysis_service.analyze(screenshot_path)
            
            if result.error:
                logger.error(f"Analysis error: {result.error}")
                return
            
            if result.item:
                # Step 3: Store data
                self.storage_service.add_item(result.item)
                logger.info(f"Item saved: {result.item.item_name}")
            else:
                logger.warning("No item data extracted from screenshot")
                
        except Exception as e:
            logger.exception(f"Error during screenshot processing: {e}")

    def start(self) -> None:
        """Start the application."""
        logger.info("Starting Screen Market Scraper...")
        logger.info(f"Press {config.HOTKEY.upper()} to capture screenshot")
        logger.info("Press Ctrl+C to stop")
        
        self._running = True
        self.hotkey_listener.start()
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Keep the main thread alive using keyboard.wait()
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.stop()

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def stop(self) -> None:
        """Stop the application."""
        logger.info("Stopping Screen Market Scraper...")
        self._running = False
        self.hotkey_listener.stop()
        logger.info("Application stopped.")


def main():
    """Application entry point."""
    app = ScreenMarketScraper()
    app.start()


if __name__ == "__main__":
    main()
