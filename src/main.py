"""Основная точка входа для приложения."""
import logging
import os
import signal
import sys
from pathlib import Path

import keyboard

from src.config import config
from src.services.screenshot_service import ScreenshotService
from src.services.image_analysis_service import ImageAnalysisService
from src.services.data_storage_service import DataStorageService
from src.services.items_catalog_service import ItemsCatalogService
from src.utils.hotkey_listener import HotkeyListener

# Путь к файлу логов
LOG_FILE = config.BASE_DIR / "app.log"

# Очистить предыдущие логи при запуске (игнорировать ошибку если файл занят)
try:
    if LOG_FILE.exists():
        LOG_FILE.unlink()
except PermissionError:
    pass  # Файл занят другим процессом, продолжим работу

# Настройка логирования в файл и консоль
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class ScreenMarketScraper:
    """Основной класс приложения."""

    def __init__(self):
        """Инициализировать приложение."""
        self._ensure_directories()
        
        self.screenshot_service = ScreenshotService()
        self.analysis_service = ImageAnalysisService()
        self.catalog_service = ItemsCatalogService()
        self.storage_service = DataStorageService(catalog_service=self.catalog_service)
        self.hotkey_listener = HotkeyListener(
            hotkey=config.HOTKEY,
            callback=self._on_screenshot_triggered
        )
        self._running = False

    def _ensure_directories(self) -> None:
        """Убедиться, что требуемые директории существуют."""
        config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Папка скриншотов: {config.SCREENSHOTS_DIR}")
        logger.info(f"Файл данных: {config.DATA_FILE}")

    def _on_screenshot_triggered(self) -> None:
        """Обработать нажатие горячей клавиши."""
        logger.info("Захват скриншота!")
        
        try:
            # Шаг 1: Захват скриншота
            screenshot_path = self.screenshot_service.capture()
            logger.info(f"Скриншот сохранён: {screenshot_path}")
            
            # Шаг 2: Анализ изображения
            result = self.analysis_service.analyze(screenshot_path)
            
            if result.error:
                logger.error(f"Ошибка анализа: {result.error}")
                return
            
            if result.item:
                # Шаг 3: Сохранение данных
                self.storage_service.add_item(result.item)
                logger.info(f"Предмет сохранён: {result.item.item_name}")
            else:
                logger.warning("Данные предмета не извлечены из скриншота")
                
        except Exception as e:
            logger.exception(f"Ошибка при обработке скриншота: {e}")

    def start(self) -> None:
        """Запустить приложение."""
        logger.info("Запуск Screen Market Scraper...")
        logger.info(f"Нажмите {config.HOTKEY.upper()} для захвата скриншота")
        logger.info("Нажмите Ctrl+C для остановки")
        
        self._running = True
        self.hotkey_listener.start()
        
        # Обработка корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Держать основной поток активным с помощью keyboard.wait()
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.stop()

    def _signal_handler(self, signum, frame) -> None:
        """Обработать сигналы завершения."""
        logger.info(f"Получен сигнал {signum}, завершение работы...")
        self.stop()

    def stop(self) -> None:
        """Остановить приложение."""
        logger.info("Остановка Screen Market Scraper...")
        self._running = False
        self.hotkey_listener.stop()
        logger.info("Приложение остановлено.")


def main():
    """Точка входа приложения."""
    app = ScreenMarketScraper()
    app.start()


if __name__ == "__main__":
    main()
