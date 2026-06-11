"""Тесты для моделей данных."""
import pytest
from src.models import MarketItem, ExtractedText, AnalysisResult


class TestMarketItem:
    """Тесты для MarketItem."""
    
    def test_create_with_city(self):
        """Создание MarketItem с городом."""
        item = MarketItem(
            city="Martlock",
            item_name="Лен",
            sell_price=50,
            buy_price=55,
            average_price=52,
            screenshot_date="2026-06-11T14:30:45"
        )
        
        assert item.city == "Martlock"
        assert item.item_name == "Лен"
        assert item.sell_price == 50
    
    def test_to_dict_includes_city(self):
        """to_dict() включает city."""
        item = MarketItem(
            city="Fort Sterling",
            item_name="Бревна сосны",
            sell_price=100,
            buy_price=150,
            average_price=125,
            screenshot_date="2026-06-11T14:30:45",
            item_tier=4,
            item_enchantment=1,
            item_quality=0
        )
        
        data = item.to_dict()
        
        assert data["screenshot_date"] == "2026-06-11T14:30:45"
        assert data["city"] == "Fort Sterling"
        assert data["item_name"] == "Бревна сосны"
        assert data["item_tier"] == 4
        assert data["item_enchantment"] == 1
        assert data["item_quality"] == 0
        assert data["sell_price"] == 100
        assert data["buy_price"] == 150
        assert data["average_price"] == 125
    
    def test_from_dict_with_city(self):
        """from_dict() читает city."""
        data = {
            "screenshot_date": "2026-06-11T14:30:45",
            "city": "Lymhurst",
            "item_name": "Дубовые бревна",
            "sell_price": 200,
            "buy_price": 180,
            "average_price": 190,
            "item_tier": 5,
            "item_enchantment": 2,
            "item_quality": 0
        }
        
        item = MarketItem.from_dict(data)
        
        assert item.city == "Lymhurst"
        assert item.item_name == "Дубовые бревна"
        assert item.sell_price == 200
    
    def test_from_dict_city_default_empty(self):
        """from_dict() с пустым city."""
        data = {
            "screenshot_date": "2026-06-11T14:30:45",
            "city": "",
            "item_name": "Лен",
            "sell_price": 50,
            "buy_price": 55,
            "average_price": 52,
            "item_tier": 3,
            "item_enchantment": 0,
            "item_quality": 0
        }
        
        item = MarketItem.from_dict(data)
        
        assert item.city == ""


class TestExtractedText:
    """Тесты для ExtractedText."""
    
    def test_default_values(self):
        """Значения по умолчанию пустые."""
        extracted = ExtractedText()
        
        assert extracted.city_text == ""
        assert extracted.title_text == ""
        assert extracted.buy_price_text == ""
        assert extracted.sell_price_text == ""
        assert extracted.avg_price_text == ""


class TestAnalysisResult:
    """Тесты для AnalysisResult."""
    
    def test_create_with_item(self):
        """Создание с MarketItem."""
        item = MarketItem(
            city="Martlock",
            item_name="Лен",
            sell_price=50,
            buy_price=55,
            average_price=52,
            screenshot_date="2026-06-11T14:30:45"
        )
        
        result = AnalysisResult(
            screenshot_path="/path/to/screenshot.png",
            item=item
        )
        
        assert result.item is not None
        assert result.item.city == "Martlock"
        assert result.error is None
    
    def test_create_with_error(self):
        """Создание с ошибкой."""
        result = AnalysisResult(
            screenshot_path="/path/to/screenshot.png",
            error="Не удалось загрузить изображение"
        )
        
        assert result.item is None
        assert result.error == "Не удалось загрузить изображение"
