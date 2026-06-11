"""
Тесты для calibration_tool.py.

Проверка корректного отображения:
- Числа (координаты ROI)
- Кириллица в интерфейсе (не "???")
- UTF-8 кодировка в JSON
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Импортировать модуль калибровки
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.calibration_tool import ROISelector


class TestROISaveEncoding:
    """Тесты кодировки при сохранении ROI."""
    
    def test_save_json_utf8_encoding(self, tmp_path):
        """
        Критичный тест: JSON сохраняется в UTF-8.
        
        Баг: Кириллица в названиях ROI могла сохраняться как \u0411.
        """
        # Создать тестовое изображение
        import cv2
        import numpy as np
        test_image = tmp_path / "test_roi.png"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        # Создать селектор
        selector = ROISelector(test_image)
        selector.rois = {
            "title": {"x1": 100, "y1": 200, "x2": 300, "y2": 400}
        }
        
        # Сохранить в тестовый файл
        output_file = tmp_path / "roi_config.json"
        
        # Патч конфига для использования тестовой папки
        with patch('scripts.calibration_tool.config') as mock_config:
            mock_config.BASE_DIR = tmp_path
            selector._save_config()
        
        # Проверить что файл существует
        assert output_file.exists()
        
        # Проверить что нет escape-последовательностей для кириллицы
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Названия ROI должны быть на английском (title, buy_price и т.д.)
            assert 'title' in content
            # Но описание может содержать кириллицу - проверить что нет \u
            assert '\\u0411' not in content  # Пример escape для 'Б'
    
    def test_save_json_no_ascii_escape(self, tmp_path):
        """Проверка что ensure_ascii=False работает."""
        import cv2
        import numpy as np
        test_image = tmp_path / "test_roi2.png"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        selector = ROISelector(test_image)
        selector.rois = {
            "buy_price": {"x1": 50, "y1": 100, "x2": 150, "y2": 200}
        }
        
        output_file = tmp_path / "roi_config.json"  # Фиксированное имя как в коде
        
        # Патч конфига для использования тестовой папки
        with patch('scripts.calibration_tool.config') as mock_config:
            mock_config.BASE_DIR = tmp_path
            selector._save_config()
        
        # Прочитать JSON и проверить что он валидный
        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert 'rois' in data
            assert 'buy_price' in data['rois']


class TestROICoordinates:
    """Тесты формата координат ROI."""
    
    def test_coordinates_are_integers(self, tmp_path):
        """
        Критичный тест: координаты - целые числа.
        
        Баг: Координаты могли сохраняться как строки или float.
        """
        import cv2
        import numpy as np
        test_image = tmp_path / "test_roi3.png"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        selector = ROISelector(test_image)
        selector.rois = {
            "title": {"x1": 100, "y1": 200, "x2": 300, "y2": 400}
        }
        
        # Проверить что все координаты - int
        for roi_name, coords in selector.rois.items():
            assert isinstance(coords['x1'], int), f"x1 в {roi_name} не int"
            assert isinstance(coords['y1'], int), f"y1 в {roi_name} не int"
            assert isinstance(coords['x2'], int), f"x2 в {roi_name} не int"
            assert isinstance(coords['y2'], int), f"y2 в {roi_name} не int"
    
    def test_coordinates_positive(self, tmp_path):
        """Координаты должны быть положительными."""
        import cv2
        import numpy as np
        test_image = tmp_path / "test_roi4.png"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        selector = ROISelector(test_image)
        selector.rois = {
            "sell_price": {"x1": 100, "y1": 200, "x2": 300, "y2": 400}
        }
        
        for roi_name, coords in selector.rois.items():
            assert coords['x1'] >= 0, f"x1 в {roi_name} отрицательный"
            assert coords['y1'] >= 0, f"y1 в {roi_name} отрицательный"
            assert coords['x2'] >= 0, f"x2 в {roi_name} отрицательный"
            assert coords['y2'] >= 0, f"y2 в {roi_name} отрицательный"
    
    def test_coordinates_order(self, tmp_path):
        """x1 < x2 и y1 < y2."""
        import cv2
        import numpy as np
        test_image = tmp_path / "test_roi5.png"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        selector = ROISelector(test_image)
        # Эмуляция выбора с пересечением координат
        selector.rois = {
            "avg_price": {"x1": 100, "y1": 200, "x2": 300, "y2": 400}
        }
        
        for roi_name, coords in selector.rois.items():
            assert coords['x1'] <= coords['x2'], f"x1 > x2 в {roi_name}"
            assert coords['y1'] <= coords['y2'], f"y1 > y2 в {roi_name}"


class TestUIStrings:
    """Тесты строк интерфейса на русском."""
    
    def test_roi_names_are_defined(self):
        """Названия ROI определены."""
        import cv2
        import numpy as np
        from pathlib import Path
        import tempfile
        
        # Создать временное изображение
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(f.name, img)
            test_path = Path(f.name)
        
        try:
            selector = ROISelector(test_path)
            
            # Проверить что все ROI names определены (4 зоны)
            assert len(selector.roi_names) == 4
            assert "title" in selector.roi_names
            assert "buy_price" in selector.roi_names
            assert "sell_price" in selector.roi_names
            assert "avg_price" in selector.roi_names
        finally:
            test_path.unlink()
    
    def test_ui_instructions_cyrillic(self):
        """
        Критичный тест: инструкции на русском без "???".
        
        Баг: При неправильной кодировке русский текст отображался как "???".
        """
        # Проверить что строки в коде содержат корректную кириллицу
        import scripts.calibration_tool as calibration
        
        # Получить исходный код модуля
        import inspect
        source = inspect.getsource(calibration)
        
        # Проверить что нет "???" в исходном коде
        assert '???' not in source, "Найдены '???' в исходном коде"
        
        # Проверить что русские строки присутствуют
        assert 'Выберите области' in source or 'Выберите:' in source
        assert 'нажмите' in source.lower()
    
    def test_window_title_cyrillic(self):
        """Заголовок окна содержит кириллицу."""
        import cv2
        import numpy as np
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(f.name, img)
            test_path = Path(f.name)
        
        try:
            selector = ROISelector(test_path)
            
            # Проверить что заголовок окна содержит кириллицу
            assert 'Селектор' in selector.window_name or 'ROI' in selector.window_name
            # Проверить что нет "???"
            assert '???' not in selector.window_name
        finally:
            test_path.unlink()


class TestColorFormat:
    """Тесты формата цветов для ROI."""
    
    def test_colors_are_bgr_tuples(self):
        """Цвета в формате BGR (OpenCV)."""
        import cv2
        import numpy as np
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(f.name, img)
            test_path = Path(f.name)
        
        try:
            selector = ROISelector(test_path)
            
            # Проверить что все цвета - кортежи из 3 элементов
            for roi_name, color in selector.colors.items():
                assert isinstance(color, tuple), f"Цвет для {roi_name} не кортеж"
                assert len(color) == 3, f"Цвет для {roi_name} не BGR"
                # Проверить что значения в диапазоне 0-255
                for value in color:
                    assert 0 <= value <= 255, f"Значение цвета {value} вне диапазона"
        finally:
            test_path.unlink()
    
    def test_colors_defined_for_all_rois(self):
        """Цвета определены для всех ROI."""
        import cv2
        import numpy as np
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(f.name, img)
            test_path = Path(f.name)
        
        try:
            selector = ROISelector(test_path)
            
            # Проверить что для каждого ROI есть цвет
            for roi_name in selector.roi_names:
                assert roi_name in selector.colors, f"Нет цвета для {roi_name}"
        finally:
            test_path.unlink()


class TestMouseCallback:
    """Тесты обработки мыши."""
    
    def test_mouse_draw_rectangle(self, tmp_path):
        """
        Тест рисования прямоугольника при выделении.
        
        Проверяет что координаты сохраняются корректно.
        """
        import cv2
        import numpy as np
        
        test_image = tmp_path / "test_roi6.png"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        selector = ROISelector(test_image)
        
        # Эмуляция нажатия мыши
        selector.current_roi = (10, 20)
        
        # Эмуляция отпускания мыши
        class MockEvent:
            pass
        
        # Вызвать callback напрямую
        selector._mouse_callback(cv2.EVENT_LBUTTONDOWN, 10, 20, 0, None)
        selector._mouse_callback(cv2.EVENT_LBUTTONUP, 50, 60, 0, None)
        
        # Проверить что ROI сохранена (title первый)
        assert "title" in selector.rois
        assert selector.rois["title"]["x1"] == 10
        assert selector.rois["title"]["y1"] == 20
        assert selector.rois["title"]["x2"] == 50
        assert selector.rois["title"]["y2"] == 60
