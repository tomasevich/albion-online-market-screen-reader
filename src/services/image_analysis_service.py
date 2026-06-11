"""Сервис для анализа скриншотов и извлечения данных."""
import json
import re
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pytesseract

from src.config import config
from src.logging_config import get_logger
from src.models import AnalysisResult, ExtractedText, MarketItem

logger = get_logger(__name__)

# Установить путь к Tesseract
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH


class ImageAnalysisService:
    """Сервис для анализа изображений и извлечения данных о рынке."""

    def __init__(self):
        """Инициализировать сервис анализа изображений."""
        self._TESSERACT_CONFIG = r'--oem 3 --psm 6'  # Предположить однородный блок текста

    def analyze(self, screenshot_path: Path) -> AnalysisResult:
        """
        Проанализировать скриншот и извлечь данные о предмете рынка.
        
        Args:
            screenshot_path: Путь к файлу скриншота.
            
        Returns:
            AnalysisResult с извлечёнными данными предмета или ошибкой.
        """
        try:
            # Загрузить изображение
            image = cv2.imread(str(screenshot_path))
            if image is None:
                return AnalysisResult(
                    screenshot_path=str(screenshot_path),
                    error="Не удалось загрузить изображение"
                )
            
            logger.info(f"Анализ изображения: {screenshot_path}")
            
            # Извлечь текст из областей
            extracted_text = self._extract_text_from_regions(image)
            
            # Вывести извлечённый текст для отладки
            self._log_extracted_text(extracted_text)
            
            # Проанализировать и создать предмет рынка
            item = self._parse_market_item(extracted_text, screenshot_path)
            
            # Сохранить отладочное изображение, если включено
            if config.DEBUG_MODE:
                self._save_debug_image(image, screenshot_path, extracted_text)
            
            return AnalysisResult(
                screenshot_path=str(screenshot_path),
                item=item,
                extracted_text=extracted_text
            )
            
        except Exception as e:
            logger.exception(f"Ошибка при анализе изображения: {e}")
            return AnalysisResult(
                screenshot_path=str(screenshot_path),
                error=str(e)
            )

    def _log_extracted_text(self, extracted: ExtractedText) -> None:
        """Вывести извлечённый текст для отладки."""
        logger.debug(f"Извлечённый текст - Название: '{extracted.title_text}'")
        logger.debug(f"Извлечённый текст - Цена покупки: '{extracted.buy_price_text}'")
        logger.debug(f"Извлечённый текст - Цена продажи: '{extracted.sell_price_text}'")
        logger.debug(f"Извлечённый текст - Средняя цена: '{extracted.avg_price_text}'")

    def _extract_text_from_regions(self, image: np.ndarray) -> ExtractedText:
        """
        Извлечь текст из разных областей изображения с использованием конфигурации ROI.
        
        Args:
            image: Изображение OpenCV (формат BGR).
            
        Returns:
            ExtractedText с текстом из каждой области.
        """
        height, width = image.shape[:2]
        
        # Получить координаты ROI из конфигурации
        rois = config.roi_coordinates
        
        # Проверить наличие корректных координат ROI
        has_valid_rois = any(
            roi.get("x1", 0) > 0 or roi.get("y1", 0) > 0 
            for roi in rois.values()
        )

        extracted = ExtractedText()
        
        if has_valid_rois:
            # Использовать настроенные координаты ROI
            logger.info("Использование настроенных координат ROI")
            
            # Область названия
            if "title" in rois and self._is_valid_roi(rois["title"]):
                title_roi = self._get_roi(image, rois["title"])
                extracted.title_text = self._ocr_text(title_roi)
            
            # Область цены покупки
            if "buy_price" in rois and self._is_valid_roi(rois["buy_price"]):
                buy_roi = self._get_roi(image, rois["buy_price"])
                extracted.buy_price_text = self._ocr_text(buy_roi)
            
            # Область цены продажи
            if "sell_price" in rois and self._is_valid_roi(rois["sell_price"]):
                sell_roi = self._get_roi(image, rois["sell_price"])
                extracted.sell_price_text = self._ocr_text(sell_roi)
            
            # Область средней цены
            if "avg_price" in rois and self._is_valid_roi(rois["avg_price"]):
                avg_roi = self._get_roi(image, rois["avg_price"])
                extracted.avg_price_text = self._ocr_text(avg_roi)
            
        else:
            # Резервный метод: использовать относительные координаты (устарело, но для обратной совместимости)
            logger.warning("Корректные координаты ROI не найдены, используется резервный метод")
            roi_right = int(width * config.ROI_RIGHT_MARGIN)
            
            # Область названия (правая сторона экрана)
            title_roi = image[0:int(height * 0.3), roi_right:int(width)]
            
            # Области цен (правая сторона)
            price_area = image[int(height * 0.2):int(height * 0.6), roi_right:int(width)]
            
            # Извлечь текст с помощью OCR
            extracted.title_text = self._ocr_text(title_roi)
            logger.debug(f"Название OCR (резервный метод): {extracted.title_text}")
            
            # Текст цен (все цены вместе)
            price_text = self._ocr_text(price_area)
            logger.debug(f"Цены OCR (резервный метод): {price_text}")
            
            # Парсинг отдельных цен из объединённого текста
            prices = self._parse_prices(price_text)
            extracted.buy_price_text = str(prices.get("buy", ""))
            extracted.sell_price_text = str(prices.get("sell", ""))
            extracted.avg_price_text = str(prices.get("avg", ""))
            
        return extracted

    def _is_valid_roi(self, roi: dict) -> bool:
        """Проверить корректность координат ROI."""
        return (
            roi.get("x1", 0) > 0 or 
            roi.get("y1", 0) > 0
        )

    def _get_roi(self, image: np.ndarray, roi: dict) -> np.ndarray:
        """Извлечь ROI из изображения."""
        x1, y1 = roi["x1"], roi["y1"]
        x2, y2 = roi["x2"], roi["y2"]
        return image[y1:y2, x1:x2]

    def _save_debug_image(
        self, 
        image: np.ndarray, 
        screenshot_path: Path,
        extracted: ExtractedText
    ) -> None:
        """Сохранить отладочное изображение с наложениями ROI и извлечённым текстом."""
        debug_image = image.copy()
        rois = config.roi_coordinates
        
        # Нарисовать прямоугольники и подписи ROI
        for name, roi in rois.items():
            if self._is_valid_roi(roi):
                color = config.COLOR_RANGES.get(name, {}).get("lower", (0, 255, 0))
                if isinstance(color, tuple) and len(color) == 3:
                    # Преобразовать из формата dict в tuple
                    color = (color[0], color[1], color[2])
                else:
                    color = (0, 255, 0)
                
                cv2.rectangle(
                    debug_image,
                    (roi["x1"], roi["y1"]),
                    (roi["x2"], roi["y2"]),
                    color,
                    2
                )
                cv2.putText(
                    debug_image,
                    name,
                    (roi["x1"], roi["y1"] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )
        
        # Добавить наложение извлечённого текста
        text_y = 30
        text_lines = [
            f"Название: {extracted.title_text[:50]}",
            f"Покупка: {extracted.buy_price_text} | Продажа: {extracted.sell_price_text} | Средняя: {extracted.avg_price_text}",
        ]
        
        for i, line in enumerate(text_lines):
            cv2.putText(
                debug_image,
                line,
                (10, text_y + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        # Сохранить отладочное изображение
        debug_path = screenshot_path.parent / f"debug_{screenshot_path.name}"
        cv2.imwrite(str(debug_path), debug_image)
        logger.debug(f"Отладочное изображение сохранено: {debug_path}")

    def _ocr_text(self, image_roi: np.ndarray) -> str:
        """
        Выполнить OCR для области изображения с предобработкой.
        
        Args:
            image_roi: Область интереса.
            
        Returns:
            Извлечённая строка текста.
        """
        if image_roi.size == 0:
            return ""
        
        # Предобработать для лучшей точности OCR
        gray = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        
        # Изменить размер для увеличения размера текста (помогает с мелким текстом)
        scale_factor = 2
        resized = cv2.resize(
            gray, 
            (0, 0), 
            fx=scale_factor, 
            fy=scale_factor,
            interpolation=cv2.INTER_CUBIC
        )

        # Адаптивное пороговое значение (лучше OTSU для разного освещения)
        binary = cv2.adaptiveThreshold(
            resized,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Размер блока (должен быть нечётным)
            2    # C
        )
        
        # Морфологические операции для соединения разорванных символов
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Выполнить OCR
        text = pytesseract.image_to_string(
            cleaned,
            lang=config.OCR_LANG,
            config=self._TESSERACT_CONFIG
        ).strip()
        
        return text

    def _parse_prices(self, text: str) -> dict:
        """
        Распарсить цены из текста OCR с учётом контекста.
        
        Ищет числа с подсказками контекста в тексте.
        
        Args:
            text: Текст OCR с ценами.
            
        Returns:
            Словарь с распарсенными ценами.
        """
        prices = {"buy": 0, "sell": 0, "avg": 0}
        
        # Паттерн для поиска чисел (обрабатывает запятую и точку как разделители тысяч)
        number_pattern = r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?'
        
        # Найти все числа с окружающим контекстом
        matches = re.finditer(number_pattern, text)
        
        numbers = []
        for match in matches:
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].lower()
            num_str = match.group().replace(',', '').replace('.', '')
            
            try:
                num = int(num_str)
                numbers.append({
                    "value": num,
                    "context": context,
                    "original": match.group()
                })
            except ValueError:
                continue
        
        # Попытаться определить каждую цену по контексту
        for item in numbers:
            ctx = item["context"]
            
            # Проверить индикаторы цены покупки
            if any(word in ctx for word in ["куп", "buy", "покуп"]):
                if prices["buy"] == 0:
                    prices["buy"] = item["value"]
            # Проверить индикаторы цены продажи
            elif any(word in ctx for word in ["прод", "sell", "прода"]):
                if prices["sell"] == 0:
                    prices["sell"] = item["value"]
            # Проверить индикаторы средней цены
            elif any(word in ctx for word in ["сред", "avg", "average", "ср"]):
                if prices["avg"] == 0:
                    prices["avg"] = item["value"]
        
        # Если есть 3+ числа и контекст не совпал, предполагаем порядок: sell, buy, avg
        if prices["sell"] == 0 and prices["buy"] == 0 and prices["avg"] == 0:
            if len(numbers) >= 3:
                prices["sell"] = numbers[0]["value"]
                prices["buy"] = numbers[1]["value"]
                prices["avg"] = numbers[2]["value"]
            elif len(numbers) == 2:
                prices["sell"] = numbers[0]["value"]
                prices["buy"] = numbers[1]["value"]
                prices["avg"] = int((numbers[0]["value"] + numbers[1]["value"]) / 2)
            elif len(numbers) == 1:
                prices["sell"] = numbers[0]["value"]
                prices["buy"] = numbers[0]["value"]
                prices["avg"] = numbers[0]["value"]
        
        return prices

    def _parse_market_item(
        self, 
        extracted: ExtractedText, 
        screenshot_path: Path
    ) -> MarketItem | None:
        """
        Создать MarketItem из извлечённого текста.
        
        Args:
            extracted: Извлечённые текстовые данные.
            screenshot_path: Путь к оригинальному скриншоту.
            
        Returns:
            MarketItem если данные корректны, иначе None.
        """
        # Очистить название предмета - убрать распространённые артефакты OCR
        item_name = extracted.title_text.strip()
        
        # Отфильтровать распространённые ошибки OCR
        if item_name in ["oy", "оу", "ou", "00", "OO", "qq", ""]:
            logger.warning(f"Обнаружено некорректное название предмета (ошибка OCR): '{item_name}'")
            return None
        
        if len(item_name) < 2:
            logger.warning(f"Название предмета слишком короткое: '{item_name}'")
            return None
        
        # Создать временную метку из имени файла
        filename = screenshot_path.stem  # например, "2025-01-15-14-30-45"
        try:
            dt = datetime.strptime(filename, "%Y-%m-%d-%H-%M-%S")
            screenshot_date = dt.strftime(config.DATE_FORMAT)
        except ValueError:
            screenshot_date = datetime.now().strftime(config.DATE_FORMAT)
        
        # Распарсить цены (на случай если они не были извлечены как числа)
        buy_price = self._safe_parse_int(extracted.buy_price_text)
        sell_price = self._safe_parse_int(extracted.sell_price_text)
        avg_price = self._safe_parse_int(extracted.avg_price_text)
        
        return MarketItem(
            item_name=item_name,
            sell_price=sell_price,
            buy_price=buy_price,
            average_price=avg_price,
            screenshot_date=screenshot_date
        )

    def _safe_parse_int(self, value: str | int) -> int:
        """Безопасно распарсить целое число из строки."""
        if isinstance(value, int):
            return value
        if not value:
            return 0
        try:
            # Убрать распространённые разделители
            cleaned = str(value).replace(',', '').replace('.', '')
            return int(cleaned)
        except (ValueError, TypeError):
            return 0
