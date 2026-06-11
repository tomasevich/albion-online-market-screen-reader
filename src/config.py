"""Configuration and constants for the application."""
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppConfig:
    """Application configuration."""
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SCREENSHOTS_DIR: Path = BASE_DIR / "screenshots"
    DATA_FILE: Path = BASE_DIR / "market_data.json"
    EXAMPLE_FILE: Path = BASE_DIR / "example.png"
    ROI_CONFIG_FILE: Path = BASE_DIR / "roi_config.json"
    
    # Hotkey configuration
    HOTKEY: str = "print_screen"
    
    # File naming format for screenshots
    SCREENSHOT_FORMAT: str = "%Y-%m-%d-%H-%M-%S.png"
    
    # JSON date format (ISO 8601)
    DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    
    # Image analysis settings
    ROI_RIGHT_MARGIN: float = 0.6  # Right 40% of screen for prices
    ROI_LEFT_MARGIN: float = 0.0   # Left side for item name
    
    # OCR settings
    OCR_LANG: str = "rus+eng"  # Russian + English
    
    # Tesseract path (Windows default installation)
    TESSERACT_PATH: str = r"C:\Users\vyach\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    
    # ROI coordinates (loaded from roi_config.json)
    roi_coordinates: dict = field(default_factory=dict)
    
    # Debug mode - save images with ROI overlays
    DEBUG_MODE: bool = True
    
    # Color ranges for region detection (BGR format for OpenCV)
    # These are example ranges - should be calibrated with example.png
    COLOR_RANGES = {
        "title": {"lower": (100, 100, 200), "upper": (200, 200, 255)},     # Blue
        "buy_price": {"lower": (0, 0, 0), "upper": (100, 100, 150)},       # Red (in BGR)
        "sell_price": {"lower": (0, 100, 0), "upper": (100, 200, 100)},    # Green
        "avg_price": {"lower": (100, 0, 100), "upper": (200, 100, 200)},   # Purple
    }
    
    def __post_init__(self):
        """Ensure directories exist and load ROI config."""
        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_roi_config()

    def _load_roi_config(self) -> None:
        """Load ROI coordinates from config file."""
        if self.ROI_CONFIG_FILE.exists():
            try:
                with open(self.ROI_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.roi_coordinates = data.get("rois", {})
            except (json.JSONDecodeError, IOError):
                pass


# Global config instance
config = AppConfig()
