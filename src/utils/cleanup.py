"""Утилиты для очистки ресурсов."""
from pathlib import Path

from src.config import config
from src.logging_config import get_logger

logger = get_logger(__name__)


def cleanup_screenshots() -> None:
    """
    Очистить папку скриншотов.
    
    Удаляет все файлы из папки screenshots.
    Вызывается при нормальном завершении программы.
    """
    screenshots_dir = config.SCREENSHOTS_DIR
    
    if not screenshots_dir.exists():
        logger.debug("Папка скриншотов не существует")
        return
    
    try:
        # Удалить все файлы и подпапки
        deleted_count = 0
        for item in screenshots_dir.iterdir():
            if item.is_file():
                item.unlink()
                deleted_count += 1
            elif item.is_dir():
                # Рекурсивно удалить подпапку
                import shutil
                shutil.rmtree(item)
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Папка screenshots очищена ({deleted_count} объектов)")
        else:
            logger.debug("Скриншоты не найдены")
            
    except (IOError, OSError) as e:
        logger.error(f"Ошибка при очистке скриншотов: {e}")
