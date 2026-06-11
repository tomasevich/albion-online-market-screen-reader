"""Configuration and constants for the application."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    """Application configuration."""
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SCREENSHOTS_DIR: Path = BASE_DIR / "screenshots"
    DATA_FILE: Path = BASE_DIR / "market_data.json"
    EXAMPLE_FILE: Path = BASE_DIR / "example.png"
    
    # Hotkey configuration
    HOTKEY: str = "printscreen"
    
    # File naming format for screenshots
    SCREENSHOT_FORMAT: str = "%Y-%m-%d-%H-%M-%S.png"
    
    # JSON date format (ISO 8601)
    DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    
    # Image analysis settings
    ROI_RIGHT_MARGIN: float = 0.6  # Right 40% of screen for prices
    ROI_LEFT_MARGIN: float = 0.0   # Left side for item name
    
    # OCR settings
    OCR_LANG: str = "rus+eng"  # Russian + English
    
    # Color ranges for region detection (BGR format for OpenCV)
    # These are example ranges - should be calibrated with example.png
    COLOR_RANGES = {
        "title": {"lower": (100, 100, 200), "upper": (200, 200, 255)},     # Blue
        "buy_price": {"lower": (0, 0, 0), "upper": (100, 100, 150)},       # Red (in BGR)
        "sell_price": {"lower": (0, 100, 0), "upper": (100, 200, 100)},    # Green
        "avg_price": {"lower": (100, 0, 100), "upper": (200, 100, 200)},   # Purple
        "tier": {"lower": (0, 100, 150), "upper": (50, 200, 255)},         # Orange
    }
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


# Global config instance
config = AppConfig()
