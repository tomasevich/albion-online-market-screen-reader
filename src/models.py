"""Data models for the application."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MarketItem:
    """Represents a market item extracted from screenshot."""
    
    item_name: str
    sell_price: int
    buy_price: int
    average_price: int
    screenshot_date: str
    item_tier: int = 0
    item_enchantment: int = 0
    item_quality: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV serialization."""
        return {
            "item_name": self.item_name,
            "sell_price": self.sell_price,
            "buy_price": self.buy_price,
            "average_price": self.average_price,
            "screenshot_date": self.screenshot_date,
            "item_tier": self.item_tier,
            "item_enchantment": self.item_enchantment,
            "item_quality": self.item_quality,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MarketItem":
        """Create instance from dictionary."""
        return cls(
            item_name=data["item_name"],
            sell_price=data["sell_price"],
            buy_price=data["buy_price"],
            average_price=data["average_price"],
            screenshot_date=data["screenshot_date"],
            item_tier=data.get("item_tier", 0),
            item_enchantment=data.get("item_enchantment", 0),
            item_quality=data.get("item_quality", 0),
        )


@dataclass
class ExtractedText:
    """Raw extracted text from image regions."""
    
    title_text: str = ""
    buy_price_text: str = ""
    sell_price_text: str = ""
    avg_price_text: str = ""


@dataclass
class AnalysisResult:
    """Result of image analysis."""
    
    screenshot_path: str
    item: Optional[MarketItem] = None
    error: Optional[str] = None
    extracted_text: Optional[ExtractedText] = None
