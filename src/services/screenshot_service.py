"""Сервис для захвата скриншотов."""
from datetime import datetime
from pathlib import Path

import mss

from src.config import config
from src.logging_config import get_logger

logger = get_logger(__name__)


class ScreenshotService:
    """Сервис для захвата скриншотов."""

    def __init__(self):
        """Инициализировать сервис скриншотов."""
        self._screenshot_counter = 0

    def capture(self) -> Path:
        """
        Захватить скриншот основного монитора.
        
        Returns:
            Путь к сохранённому файлу скриншота.
        """
        # Генерировать имя файла
        timestamp = datetime.now()
        filename = timestamp.strftime(config.SCREENSHOT_FORMAT)
        filepath = config.SCREENSHOTS_DIR / filename
        
        # Захват экрана с помощью mss (быстро и эффективно)
        with mss.mss() as sct:
            # Получить основной монитор
            monitor = sct.monitors[1]  # monitors[0] — все мониторы
            
            # Захватить и сохранить
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
        
        self._screenshot_counter += 1
        logger.info(f"Скриншот #{self._screenshot_counter} захвачен: {filepath}")
        
        return filepath
