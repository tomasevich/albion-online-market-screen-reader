"""Прослушиватель горячих клавиш для глобальных событий клавиатуры."""
import logging
from typing import Callable

import keyboard

from src.logging_config import get_logger

logger = get_logger(__name__)


class HotkeyListener:
    """Сервис для прослушивания глобальных нажатий горячих клавиш."""

    def __init__(self, hotkey: str, callback: Callable):
        """
        Инициализировать прослушиватель горячих клавиш.
        
        Args:
            hotkey: Комбинация горячей клавиши (например, "printscreen").
            callback: Функция для вызова при нажатии горячей клавиши.
        """
        self._hotkey = hotkey
        self._callback = callback
        self._running = False

    def start(self) -> None:
        """Запустить прослушивание нажатий горячих клавиш."""
        if self._running:
            logger.warning("Прослушиватель горячих клавиш уже запущен")
            return
        
        logger.info(f"Прослушивание горячей клавиши: {self._hotkey}")
        
        # Зарегистрировать callback горячей клавиши
        keyboard.add_hotkey(
            self._hotkey,
            self._on_hotkey_pressed,
            suppress=False  # Разрешить прохождение клавиши
        )
        
        self._running = True
        
        logger.info("Прослушиватель горячих клавиш запущен")

    def stop(self) -> None:
        """Остановить прослушивание нажатий горячих клавиш."""
        if not self._running:
            return
        
        logger.info("Остановка прослушивателя горячих клавиш...")
        self._running = False
        
        # Удалить горячую клавишу
        keyboard.remove_hotkey(self._hotkey)
        
        logger.info("Прослушиватель горячих клавиш остановлен")

    def _on_hotkey_pressed(self) -> None:
        """Обработать нажатие горячей клавиши."""
        if not self._running:
            return
        
        try:
            self._callback()
        except Exception as e:
            logger.exception(f"Ошибка в callback горячей клавиши: {e}")

