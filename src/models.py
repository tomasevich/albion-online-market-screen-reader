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
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "item_name": self.item_name,
            "sell_price": self.sell_price,
            "buy_price": self.buy_price,
            "average_price": self.average_price,
            "screenshot_date": self.screenshot_date,
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
