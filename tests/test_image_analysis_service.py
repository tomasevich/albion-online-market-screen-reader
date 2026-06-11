"""
Тесты для ImageAnalysisService.

Основаны на реальных багах:
- Очистка названия предмета от артефактов OCR
- Удаление символа ‚ из названия перед записью в CSV
"""
import pytest
from src.services.image_analysis_service import ImageAnalysisService


class TestCleanItemName:
    """Тесты очистки названия предмета."""
    
    def test_clean_removes_u201A_artifact(self):
        """
        Критичный тест: удаление символа ‚ (U+201A).
        
        Баг: OCR добавлял символ ‚ перед названием предмета.
        Исправление: _clean_item_name() удаляет артефакты.
        """
        service = ImageAnalysisService()
        result = service._clean_item_name("‚Бревна сосны")
        assert result == "Бревна сосны"
    
    def test_clean_removes_leading_space_and_artifact(self):
        """Удаление пробела и артефакта."""
        service = ImageAnalysisService()
        # Сначала артефакт, потом пробел (реальный кейс)
        result = service._clean_item_name("‚ Рваная шкура")
        assert result == "Рваная шкура"
    
    def test_clean_removes_multiple_spaces(self):
        """Удаление лишних пробелов."""
        service = ImageAnalysisService()
        result = service._clean_item_name("  Бревна   сосны  ")
        assert result == "Бревна сосны"
    
    def test_clean_preserves_clean_name(self):
        """Чистое название не меняется."""
        service = ImageAnalysisService()
        result = service._clean_item_name("Бревна сосны")
        assert result == "Бревна сосны"
    
    def test_clean_removes_zero_width_space(self):
        """Удаление zero-width space (U+200B)."""
        service = ImageAnalysisService()
        result = service._clean_item_name("\u200BБревна сосны")
        assert result == "Бревна сосны"
    
    def test_clean_removes_bom(self):
        """Удаление BOM (U+FEFF)."""
        service = ImageAnalysisService()
        result = service._clean_item_name("\uFEFFБревна сосны")
        assert result == "Бревна сосны"
    
    def test_clean_combined_artifacts(self):
        """Комбинация артефактов."""
        service = ImageAnalysisService()
        result = service._clean_item_name("‚\u200B\uFEFF  Лен  ")
        assert result == "Лен"
    
    def test_clean_empty_string(self):
        """Обработка пустой строки."""
        service = ImageAnalysisService()
        result = service._clean_item_name("")
        assert result == ""
    
    def test_clean_only_artifacts(self):
        """Строка только из артефактов."""
        service = ImageAnalysisService()
        result = service._clean_item_name("‚\u200B\uFEFF   ")
        assert result == ""


class TestParseMarketItem:
    """Тесты создания MarketItem."""
    
    def test_parse_item_with_clean_name(self, tmp_path):
        """Создание предмета с очищенным названием."""
        service = ImageAnalysisService()
        
        # Создать тестовый скриншот (пустой файл для теста)
        screenshot = tmp_path / "2026-06-11-19-00-00.png"
        screenshot.touch()
        
        # Создать ExtractedText (город теперь не из OCR)
        from src.models import ExtractedText
        extracted = ExtractedText()
        extracted.title_text = "‚Бревна сосны"
        extracted.buy_price_text = "100"
        extracted.sell_price_text = "150"
        extracted.avg_price_text = "125"
        
        item = service._parse_market_item(extracted, screenshot)
        
        assert item is not None
        assert item.city == ""  # Город теперь из конфига
        assert item.item_name == "Бревна сосны"  # Без артефакта!
        assert item.buy_price == 100
        assert item.sell_price == 150
        assert item.average_price == 125
    
    def test_parse_item_rejects_invalid_ocr(self, tmp_path):
        """Отклонение некорректных OCR-распознаний."""
        service = ImageAnalysisService()
        
        screenshot = tmp_path / "2026-06-11-19-00-01.png"
        screenshot.touch()
        
        from src.models import ExtractedText
        extracted = ExtractedText()
        extracted.title_text = "oy"  # Распространённая ошибка OCR
        extracted.buy_price_text = "100"
        extracted.sell_price_text = "150"
        extracted.avg_price_text = "125"
        
        item = service._parse_market_item(extracted, screenshot)
        
        assert item is None  # Должен вернуть None
    
    def test_parse_item_rejects_short_name(self, tmp_path):
        """Отклонение слишком короткого названия."""
        service = ImageAnalysisService()
        
        screenshot = tmp_path / "2026-06-11-19-00-02.png"
        screenshot.touch()
        
        from src.models import ExtractedText
        extracted = ExtractedText()
        extracted.title_text = "A"  # Слишком короткое
        extracted.buy_price_text = "100"
        extracted.sell_price_text = "150"
        extracted.avg_price_text = "125"
        
        item = service._parse_market_item(extracted, screenshot)
        
        assert item is None
    
    def test_parse_item_default_prices(self, tmp_path):
        """Цены по умолчанию при пустых значениях."""
        service = ImageAnalysisService()
        
        screenshot = tmp_path / "2026-06-11-19-00-03.png"
        screenshot.touch()
        
        from src.models import ExtractedText
        extracted = ExtractedText()
        extracted.title_text = "Бревна сосны"
        extracted.buy_price_text = ""
        extracted.sell_price_text = ""
        extracted.avg_price_text = ""
        
        item = service._parse_market_item(extracted, screenshot)
        
        assert item is not None
        assert item.city == ""  # Город теперь из конфига
        assert item.buy_price == 0
        assert item.sell_price == 0
        assert item.average_price == 0


class TestSafeParseInt:
    """Тесты безопасного парсинга целых чисел."""
    
    def test_parse_int_from_string(self):
        """Парсинг целого числа из строки."""
        service = ImageAnalysisService()
        result = service._safe_parse_int("100")
        assert result == 100
    
    def test_parse_int_from_int(self):
        """Парсинг целого числа из int."""
        service = ImageAnalysisService()
        result = service._safe_parse_int(100)
        assert result == 100
    
    def test_parse_int_with_comma(self):
        """Парсинг числа с запятой (разделитель тысяч)."""
        service = ImageAnalysisService()
        result = service._safe_parse_int("1,000")
        assert result == 1000
    
    def test_parse_int_with_dot(self):
        """Парсинг числа с точкой (разделитель тысяч)."""
        service = ImageAnalysisService()
        result = service._safe_parse_int("1.000")
        assert result == 1000
    
    def test_parse_int_empty_string(self):
        """Парсинг пустой строки."""
        service = ImageAnalysisService()
        result = service._safe_parse_int("")
        assert result == 0
    
    def test_parse_int_none(self):
        """Парсинг None."""
        service = ImageAnalysisService()
        result = service._safe_parse_int(None)
        assert result == 0

    def test_parse_int_invalid(self):
        """Парсинг некорректной строки."""
        service = ImageAnalysisService()
        result = service._safe_parse_int("abc")
        assert result == 0
