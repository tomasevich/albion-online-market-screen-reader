"""Configuration and constants for the application."""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()


@dataclass
class AppConfig:
    """Application configuration."""
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SCREENSHOTS_DIR: Path = field(init=False)
    DATA_FILE: Path = field(init=False)
    EXAMPLE_FILE: Path = field(init=False)
    ROI_CONFIG_FILE: Path = field(init=False)
    
    # Hotkey configuration
    HOTKEY: str = field(init=False)
    
    # File naming format for screenshots
    SCREENSHOT_FORMAT: str = "%Y-%m-%d-%H-%M-%S.png"
    
    # JSON date format (ISO 8601)
    DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    
    # Image analysis settings
    ROI_RIGHT_MARGIN: float = 0.6  # Right 40% of screen for prices
    ROI_LEFT_MARGIN: float = 0.0   # Left side for item name
    
    # OCR settings
    OCR_LANG: str = field(init=False)
    
    # Tesseract path (Windows default installation)
    TESSERACT_PATH: str = field(init=False)
    
    # ROI coordinates (loaded from roi_config.json)
    roi_coordinates: dict = field(default_factory=dict)
    
    # Debug mode - save images with ROI overlays
    DEBUG_MODE: bool = field(init=False)
    
    # Color ranges for region detection (BGR format for OpenCV)
    # These are example ranges - should be calibrated with example.png
    COLOR_RANGES = {
        "title": {"lower": (100, 100, 200), "upper": (200, 200, 255)},     # Blue
        "buy_price": {"lower": (0, 0, 0), "upper": (100, 100, 150)},       # Red (in BGR)
        "sell_price": {"lower": (0, 100, 0), "upper": (100, 200, 100)},    # Green
        "avg_price": {"lower": (100, 0, 100), "upper": (200, 100, 200)},   # Purple
    }
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        # Paths from environment
        self.SCREENSHOTS_DIR = Path(os.getenv("SCREENSHOTS_DIR", "screenshots"))
        if not self.SCREENSHOTS_DIR.is_absolute():
            self.SCREENSHOTS_DIR = self.BASE_DIR / self.SCREENSHOTS_DIR
            
        self.DATA_FILE = Path(os.getenv("DATA_FILE", "market_data.csv"))
        if not self.DATA_FILE.is_absolute():
            self.DATA_FILE = self.BASE_DIR / self.DATA_FILE
            
        self.EXAMPLE_FILE = Path(os.getenv("EXAMPLE_FILE", "example.png"))
        if not self.EXAMPLE_FILE.is_absolute():
            self.EXAMPLE_FILE = self.BASE_DIR / self.EXAMPLE_FILE
            
        self.ROI_CONFIG_FILE = Path(os.getenv("ROI_CONFIG_FILE", "roi_config.json"))
        if not self.ROI_CONFIG_FILE.is_absolute():
            self.ROI_CONFIG_FILE = self.BASE_DIR / self.ROI_CONFIG_FILE
        
        # Ensure screenshots directory exists
        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Hotkey from environment
        self.HOTKEY = os.getenv("HOTKEY", "print_screen")
        
        # OCR settings from environment
        self.OCR_LANG = os.getenv("OCR_LANG", "rus+eng")
        
        # Tesseract path from environment
        self.TESSERACT_PATH = os.getenv(
            "TESSERACT_PATH",
            r"C:\Users\vyach\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
        )
        
        # Debug mode from environment
        debug_value = os.getenv("DEBUG_MODE", "false").lower()
        self.DEBUG_MODE = debug_value in ("true", "1", "yes")
        
        # Load ROI config
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
