"""
Тесты для утилиты put_cyrillic_text.

Проверка корректного отображения кириллицы на изображениях.
"""
import pytest
import cv2
import numpy as np
from pathlib import Path
from src.utils.cyrillic_text import put_cyrillic_text, put_cyrillic_text_with_background, DEFAULT_FONT


class TestCyrillicText:
    """Тесты базовой функции put_cyrillic_text."""
    
    def test_font_exists(self):
        """
        Критичный тест: шрифт с кириллицей доступен.
        
        Проверяет что хотя бы один шрифт из списка существует.
        """
        assert DEFAULT_FONT is not None, "Шрифт с поддержкой кириллицы не найден"
        assert Path(DEFAULT_FONT).exists(), f"Шрифт не существует: {DEFAULT_FONT}"
    
    def test_put_cyrillic_text_returns_image(self):
        """Функция возвращает изображение."""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        result = put_cyrillic_text(image, "Тест", (10, 10))
        
        assert isinstance(result, np.ndarray)
        assert result.shape == image.shape
    
    def test_put_cyrillic_text_preserves_size(self):
        """Размер изображения не меняется."""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        result = put_cyrillic_text(image, "Тест", (10, 10))
        
        assert result.shape == image.shape
    
    def test_put_cyrillic_text_cyrillic(self):
        """
        Критичный тест: кириллица отображается.
        
        Проверяет что функция не вызывает ошибок с русским текстом.
        """
        image = np.zeros((100, 300, 3), dtype=np.uint8)
        result = put_cyrillic_text(image, "Привет мир", (10, 30), font_size=20)
        
        assert result.shape == image.shape
        # Изображение должно измениться (добавился текст)
        assert not np.array_equal(result, image)
    
    def test_put_cyrillic_text_mixed(self):
        """Смешанный текст (кириллица + латиница + цифры)."""
        image = np.zeros((100, 300, 3), dtype=np.uint8)
        result = put_cyrillic_text(image, "Тест ABC 123", (10, 30), font_size=20)
        
        assert result.shape == image.shape
        assert not np.array_equal(result, image)
    
    def test_put_cyrillic_text_colors(self):
        """Разные цвета текста."""
        image = np.zeros((100, 300, 3), dtype=np.uint8)
        
        # Белый текст
        result_white = put_cyrillic_text(image, "Тест", (10, 10), color=(255, 255, 255))
        # Красный текст (BGR)
        result_red = put_cyrillic_text(image, "Тест", (10, 10), color=(0, 0, 255))
        # Зелёный текст (BGR)
        result_green = put_cyrillic_text(image, "Тест", (10, 10), color=(0, 255, 0))
        
        # Результаты должны отличаться
        assert not np.array_equal(result_white, result_red)
        assert not np.array_equal(result_white, result_green)
    
    def test_put_cyrillic_text_font_sizes(self):
        """Разные размеры шрифта."""
        image = np.zeros((200, 300, 3), dtype=np.uint8)
        
        result_small = put_cyrillic_text(image, "Тест", (10, 10), font_size=12)
        result_large = put_cyrillic_text(image, "Тест", (10, 10), font_size=36)
        
        assert result_small.shape == image.shape
        assert result_large.shape == image.shape
        # Изображения должны отличаться (разный размер текста)
        assert not np.array_equal(result_small, result_large)
    
    def test_put_cyrillic_text_empty_string(self):
        """Пустая строка не вызывает ошибок."""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        result = put_cyrillic_text(image, "", (10, 10))
        
        assert result.shape == image.shape
    
    def test_put_cyrillic_text_special_chars(self):
        """Специальные символы и эмодзи."""
        image = np.zeros((100, 300, 3), dtype=np.uint8)
        result = put_cyrillic_text(image, "Тест! @#$%", (10, 30), font_size=20)
        
        assert result.shape == image.shape


class TestCyrillicTextWithBackground:
    """Тесты функции с полупрозрачным фоном."""
    
    def test_returns_image(self):
        """Функция возвращает изображение."""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        result = put_cyrillic_text_with_background(image, "Тест", (10, 10))
        
        assert isinstance(result, np.ndarray)
        assert result.shape == image.shape
    
    def test_preserves_size(self):
        """Размер изображения не меняется."""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        result = put_cyrillic_text_with_background(image, "Тест", (10, 10))
        
        assert result.shape == image.shape
    
    def test_cyrillic_with_background(self):
        """Кириллица с фоном."""
        image = np.zeros((100, 300, 3), dtype=np.uint8)
        result = put_cyrillic_text_with_background(
            image, "Привет мир", (10, 30),
            font_size=20,
            text_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_alpha=0.7
        )
        
        assert result.shape == image.shape
        assert not np.array_equal(result, image)
    
    def test_background_alpha(self):
        """Разная прозрачность фона."""
        # Использовать светлый фон чтобы текст был виден
        image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        
        result_opaque = put_cyrillic_text_with_background(
            image, "Тест", (10, 30),
            font_size=20,
            text_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_alpha=1.0
        )
        result_transparent = put_cyrillic_text_with_background(
            image, "Тест", (10, 30),
            font_size=20,
            text_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_alpha=0.3
        )
        
        # Изображения должны отличаться
        assert not np.array_equal(result_opaque, result_transparent)


class TestIntegration:
    """Интеграционные тесты."""
    
    def test_multiple_texts(self):
        """Несколько текстов на одном изображении."""
        image = np.zeros((200, 400, 3), dtype=np.uint8)
        
        result = put_cyrillic_text(image, "Текст 1", (10, 30), font_size=20)
        result = put_cyrillic_text(result, "Текст 2", (10, 70), font_size=20)
        result = put_cyrillic_text(result, "Текст 3", (10, 110), font_size=20)
        
        assert result.shape == image.shape
    
    def test_overlay_on_real_image(self, tmp_path):
        """Наложение текста на реальное изображение."""
        # Создать тестовое изображение
        test_image = tmp_path / "test.png"
        img = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        # Загрузить и добавить текст
        image = cv2.imread(str(test_image))
        result = put_cyrillic_text(image, "Калибровка ROI", (50, 50), font_size=28)
        
        assert result.shape == image.shape
