"""Централизованная настройка логирования для приложения."""
import logging
import os
import re
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

from src.config import config


def setup_logging() -> logging.Logger:
    """
    Настроить централизованное логирование.
    
    Возвращает:
        Logger instance для использования в модулях.
    """
    # Путь к файлу логов
    log_dir = config.BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    # Проверить, что файл не занят (попытка открыть на запись)
    try:
        if log_file.exists():
            # Попробовать открыть файл для записи
            with open(log_file, "a", encoding="utf-8") as f:
                pass
    except PermissionError:
        # Если файл занят, создаём новый с временной меткой
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"app_{timestamp}.log"
    
    # Настроить root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Очистить существующие handlers (если есть)
    root_logger.handlers.clear()
    
    # Создать форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # FileHandler с ротацией по времени (ежедневно)
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # Хранить логи 30 дней
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # StreamHandler для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Добавить handlers к root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Пытаемся валидировать путь к Tesseract и логируем предупреждение если проблема
    tesseract_path = config.TESSERACT_PATH
    if not os.path.exists(tesseract_path):
        logger = logging.getLogger(__name__)
        logger.warning(f"Tesseract не найден по пути: {tesseract_path}")
        logger.warning("Пожалуйста, настройте правильный путь в .env файле")
    
    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger для модуля.
    
    Args:
        name: Имя модуля (обычно __name__)
    
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
