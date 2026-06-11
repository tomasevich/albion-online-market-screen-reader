#!/usr/bin/env python3
"""Инструмент калибровки для определения областей ROI на example.png.

Позволяет вручную выбрать области для OCR путём рисования прямоугольников
на примере изображения и сохранения координат в конфиг.

Использование:
    python scripts/calibration_tool.py
"""
import json
import logging
from pathlib import Path

import cv2

from src.config import config

# Путь к файлу логов
LOG_FILE = config.BASE_DIR / "app.log"

# Настройка логирования в файл и консоль
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ROISelector:
    """Интерактивный инструмент для выбора областей ROI на изображении."""

    def __init__(self, image_path: Path):
        """
        Инициализировать селектор ROI.
        
        Args:
            image_path: Путь к изображению для аннотации.
        """
        self.image_path = image_path
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise ValueError(f"Не удалось загрузить изображение: {image_path}")
        
        self.original = self.image.copy()
        self.current_roi = None
        self.rois = {}
        
        # Названия областей ROI для игрового интерфейса
        self.roi_names = [
            "title",      # Синий блок - название предмета
            "buy_price",  # Красный блок - цена покупки
            "sell_price", # Зелёный блок - цена продажи
            "avg_price",  # Фиолетовый блок - средняя цена
        ]
        
        self.current_roi_index = 0
        self.window_name = "Селектор ROI - Выберите области"
        
        # Цвета для каждой ROI (формат BGR)
        self.colors = {
            "title": (255, 0, 0),      # Синий
            "buy_price": (0, 0, 255),  # Красный
            "sell_price": (0, 255, 0), # Зелёный
            "avg_price": (255, 0, 255),# Фиолетовый
        }

    def _get_current_roi_name(self) -> str:
        """Получить название текущей выбираемой ROI."""
        if self.current_roi_index < len(self.roi_names):
            return self.roi_names[self.current_roi_index]
        return ""

    def _mouse_callback(self, event, x, y, flags, param):
        """Обработать события мыши для выбора ROI."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_roi = (x, y)
            
        elif event == cv2.EVENT_LBUTTONUP:
            if self.current_roi:
                x1, y1 = self.current_roi
                x2, y2 = x, y
                
                roi_name = self._get_current_roi_name()
                
                # Пропустить если все ROI уже выбраны
                if not roi_name:
                    return
                
                self.rois[roi_name] = {
                    "x1": min(x1, x2),
                    "y1": min(y1, y2),
                    "x2": max(x1, x2),
                    "y2": max(y1, y2),
                }
                
                # Нарисовать ROI на изображении
                self._draw_all_rois()
                
                logger.info(f"Сохранена область '{roi_name}': {self.rois[roi_name]}")
                
                # Перейти к следующей ROI
                self.current_roi_index += 1
                
                if self.current_roi_index >= len(self.roi_names):
                    logger.info("Все области выбраны!")
                    self._save_config()
                    cv2.putText(
                        self.image,
                        "ГОТОВО - нажмите 'q' для выхода",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )
                
                self.current_roi = None

    def _draw_all_rois(self):
        """Нарисовать все выбранные ROI на изображении."""
        self.image = self.original.copy()
        
        for name, roi in self.rois.items():
            color = self.colors.get(name, (255, 255, 255))
            cv2.rectangle(
                self.image,
                (roi["x1"], roi["y1"]),
                (roi["x2"], roi["y2"]),
                color,
                2
            )
            cv2.putText(
                self.image,
                name,
                (roi["x1"], roi["y1"] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )

    def _save_config(self):
        """Сохранить координаты ROI в файл конфигурации."""
        output_file = config.BASE_DIR / "roi_config.json"
        
        roi_data = {
            "description": "Координаты областей ROI для OCR. Настройте их в зависимости от разрешения экрана.",
            "note": "Координаты указаны в пикселях от левого верхнего угла",
            "rois": self.rois
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(roi_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Конфигурация сохранена: {output_file}")

    def run(self):
        """Запустить интерактивный выбор ROI."""
        logger.info(f"Открытие изображения: {self.image_path}")
        logger.info(f"Выберите области в следующем порядке: {', '.join(self.roi_names)}")
        logger.info("Нажмите и перетащите для выбора области, затем отпустите кнопку мыши.")
        
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
        
        while True:
            # Отобразить инструкции
            display_image = self.image.copy()
            current_name = self._get_current_roi_name()
            
            if current_name:
                cv2.putText(
                    display_image,
                    f"Выберите: {current_name}",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )
                cv2.putText(
                    display_image,
                    f"Прогресс: {self.current_roi_index}/{len(self.roi_names)}",
                    (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
            
            cv2.imshow(self.window_name, display_image)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                logger.info("Выход...")
                break
            elif key == ord('r'):
                # Сбросить все выделения
                self.rois = {}
                self.current_roi_index = 0
                self.current_roi = None
                self.image = self.original.copy()
                logger.info("Сброс - начните выбор заново")
            elif key == ord('u'):
                # Отменить последнее выделение
                if self.rois and self.current_roi_index > 0:
                    self.current_roi_index -= 1
                    roi_name = self.roi_names[self.current_roi_index]
                    if roi_name in self.rois:
                        del self.rois[roi_name]
                    self.image = self.original.copy()
                    self._draw_all_rois()
                    logger.info(f"Отменено: {roi_name}")
        
        cv2.destroyAllWindows()


def main():
    """Точка входа для инструмента калибровки."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    example_path = config.EXAMPLE_FILE
    
    if not example_path.exists():
        logger.error(f"Файл примера не найден: {example_path}")
        logger.info("Убедитесь, что example.png существует в корне проекта.")
        return
    
    selector = ROISelector(example_path)
    selector.run()


if __name__ == "__main__":
    main()
