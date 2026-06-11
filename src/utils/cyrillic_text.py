"""Утилита для отображения кириллического текста на изображениях OpenCV.

OpenCV cv2.putText() не поддерживает кириллицу, поэтому используем PIL/Pillow
для рендеринга текста с русскими символами поверх изображения.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


# Путь к шрифту с поддержкой кириллицы
# Используем Arial.ttf который есть в Windows по умолчанию
FONT_PATHS = [
    Path("C:/Windows/Fonts/arial.ttf"),      # Windows
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),  # Linux
    Path("/System/Library/Fonts/Helvetica.ttc"),  # macOS
]

# Шрифт по умолчанию
DEFAULT_FONT = None
for font_path in FONT_PATHS:
    if font_path.exists():
        DEFAULT_FONT = str(font_path)
        break

if DEFAULT_FONT is None:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Шрифт для кириллицы не найден! Будет использоваться системный шрифт по умолчанию.")


def put_cyrillic_text(
    image: np.ndarray,
    text: str,
    position: tuple[int, int],
    font_size: int = 20,
    color: tuple[int, int, int] = (0, 255, 255),  # Жёлтый по умолчанию (BGR)
    font_path: str | None = None
) -> np.ndarray:
    """
    Отобразить текст с поддержкой кириллицы на изображении OpenCV.
    
    Args:
        image: Изображение в формате OpenCV (BGR, numpy array).
        text: Текст для отображения (поддерживает кириллицу).
        position: Координаты (x, y) левого верхнего угла текста.
        font_size: Размер шрифта в пикселях.
        color: Цвет текста в формате BGR (OpenCV).
        font_path: Путь к TTF-шрифту. Если None, используется шрифт по умолчанию.
    
    Returns:
        Изображение с нанесённым текстом (копия изображения).
    
    Example:
        >>> image = cv2.imread("image.png")
        >>> image = put_cyrillic_text(image, "Привет", (50, 50), font_size=24)
    """
    # Создать копию изображения для модификации
    result = image.copy()
    
    # Конвертировать BGR -> RGB для PIL
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(result_rgb)
    
    # Создать объект для рисования
    draw = ImageDraw.Draw(pil_image)
    
    # Выбрать шрифт
    if font_path is None:
        font_path = DEFAULT_FONT
    
    # Загрузить шрифт
    try:
        font = ImageFont.truetype(font_path, font_size)
    except (IOError, OSError):
        # Если шрифт не найден, использовать шрифт по умолчанию
        font = ImageFont.load_default()
    
    # Конвертировать цвет из BGR (OpenCV) в RGB (PIL)
    color_rgb = (color[2], color[1], color[0])
    
    # Нарисовать текст
    draw.text(position, text, font=font, fill=color_rgb)
    
    # Конвертировать обратно в OpenCV формат (BGR)
    result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    return result


def put_cyrillic_text_with_background(
    image: np.ndarray,
    text: str,
    position: tuple[int, int],
    font_size: int = 20,
    text_color: tuple[int, int, int] = (255, 255, 255),
    bg_color: tuple[int, int, int] = (0, 0, 0),
    bg_alpha: float = 0.7,
    font_path: str | None = None
) -> np.ndarray:
    """
    Отобразить текст с полупрозрачным фоном для лучшей читаемости.
    
    Args:
        image: Изображение в формате OpenCV (BGR).
        text: Текст для отображения.
        position: Координаты (x, y) левого верхнего угла.
        font_size: Размер шрифта.
        text_color: Цвет текста (BGR).
        bg_color: Цвет фона (BGR).
        bg_alpha: Прозрачность фона (0.0 - 1.0).
        font_path: Путь к TTF-шрифту.
    
    Returns:
        Изображение с текстом и фоном.
    """
    # Конвертировать BGR -> RGB для PIL
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(pil_image)
    
    # Выбрать шрифт
    if font_path is None:
        font_path = DEFAULT_FONT
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()
    
    # Получить размер текста
    bbox = draw.textbbox(position, text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Добавить отступы
    padding = 4
    x1, y1 = position[0] - padding, position[1] - padding
    x2, y2 = position[0] + text_width + padding, position[1] + text_height + padding
    
    # Конвертировать цвета
    text_color_rgb = (text_color[2], text_color[1], text_color[0])
    bg_color_rgb = (bg_color[2], bg_color[1], bg_color[0])
    
    # Нарисовать полупрозрачный фон
    overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [x1, y1, x2, y2],
        fill=(*bg_color_rgb, int(255 * bg_alpha))
    )
    
    # Наложить фон на изображение
    pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay)
    
    # Нарисовать текст поверх фона
    draw = ImageDraw.Draw(pil_image)
    draw.text(position, text, font=font, fill=text_color_rgb)
    
    # Конвертировать обратно в OpenCV
    image_with_text = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)
    
    return image_with_text
