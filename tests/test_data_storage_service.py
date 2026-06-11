"""
Тесты для DataStorageService.

Основаны на реальных багах которые были исправлены:
- CSV encoding (UTF-8 без BOM)
- Формат чисел (целые без десятичных)
- Обработка NaN значений
"""
import pytest
import pandas as pd
from pathlib import Path
from src.services.data_storage_service import DataStorageService, CSV_COLUMNS


class TestConvertDtypes:
    """Тесты приведения типов данных."""
    
    def test_convert_string_to_int(self):
        """Преобразование строки в int."""
        service = DataStorageService()
        service._df = pd.DataFrame({
            'sell_price': ['100', '200', '300'],
            'buy_price': ['150', '250', '350'],
            'average_price': ['125', '225', '325'],
            'item_tier': ['2', '3', '4'],
            'item_enchantment': ['0', '1', '2'],
            'item_quality': ['0', '0', '0'],
            'item_name': ['Лен', 'Пенька', 'Хлопок'],
            'screenshot_date': ['2026-06-11', '2026-06-11', '2026-06-11']
        })
        
        service._convert_dtypes()
        
        assert service._df['sell_price'].dtype == 'int64'
        assert service._df['sell_price'].iloc[0] == 100
        assert service._df['buy_price'].iloc[1] == 250
    
    def test_convert_none_to_zero(self):
        """Преобразование None/NaN в 0."""
        service = DataStorageService()
        service._df = pd.DataFrame({
            'sell_price': [100, None, 300],
            'buy_price': [150, 250, None],
            'average_price': [None, None, None],
            'item_tier': [2, 0, 4],
            'item_enchantment': [0, 1, 0],
            'item_quality': [0, 0, 0],
            'item_name': ['Лен', 'Пенька', 'Хлопок'],
            'screenshot_date': ['2026-06-11', '2026-06-11', '2026-06-11']
        })
        
        service._convert_dtypes()
        
        assert service._df['sell_price'].iloc[1] == 0
        assert service._df['buy_price'].iloc[2] == 0
        assert service._df['average_price'].iloc[0] == 0
    
    def test_convert_float_to_int(self):
        """Преобразование float в int."""
        service = DataStorageService()
        service._df = pd.DataFrame({
            'sell_price': [100.5, 200.9, 300.1],
            'buy_price': [150.0, 250.5, 350.9],
            'average_price': [125.5, 225.5, 325.5],
            'item_tier': [2.0, 3.0, 4.0],
            'item_enchantment': [0.0, 1.0, 2.0],
            'item_quality': [0.0, 0.0, 0.0],
            'item_name': ['Лен', 'Пенька', 'Хлопок'],
            'screenshot_date': ['2026-06-11', '2026-06-11', '2026-06-11']
        })
        
        service._convert_dtypes()
        
        assert service._df['sell_price'].dtype == 'int64'
        assert service._df['sell_price'].iloc[0] == 100
        assert service._df['buy_price'].iloc[1] == 250
    
    def test_convert_empty_dataframe(self):
        """Обработка пустого DataFrame."""
        service = DataStorageService()
        service._df = pd.DataFrame(columns=CSV_COLUMNS)
        
        # Не должно вызвать ошибок
        service._convert_dtypes()
        
        assert len(service._df) == 0


class TestSaveCsvFormat:
    """Тесты формата CSV файла."""
    
    def test_save_has_bom(self, tmp_path):
        """
        Критичный тест: CSV с BOM для Excel.
        
        Требование: UTF-8 с BOM для корректного отображения кириллицы в Excel.
        """
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        service._df = pd.DataFrame([{
            'item_name': 'Бревна сосны',
            'sell_price': 100,
            'buy_price': 150,
            'average_price': 125,
            'screenshot_date': '2026-06-11',
            'item_tier': 4,
            'item_enchantment': 0,
            'item_quality': 0
        }])
        service._save_data()
        
        # Проверить наличие BOM (первые 3 байта)
        with open(csv_file, 'rb') as f:
            bom = f.read(3)
            assert bom == b'\xef\xbb\xbf', "Файл должен начинаться с UTF-8 BOM для Excel"
        
    def test_save_integer_format(self, tmp_path):
        """
        Критичный тест: целые числа без десятичных.
        
        Баг: pandas сохранял числа как 100.0 вместо 100.
        """
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        service._df = pd.DataFrame([{
            'item_name': 'Бревна сосны',
            'sell_price': 100,
            'buy_price': 150,
            'average_price': 125,
            'screenshot_date': '2026-06-11',
            'item_tier': 4,
            'item_enchantment': 0,
            'item_quality': 0
        }])
        service._save_data()
        
        # Прочитать файл и проверить формат
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            # Числа должны быть без .0 (в кавычках или без)
            assert '"100"' in content or '100;' in content
            assert '100.0' not in content
            # Разделитель точка с запятой для Excel
            assert ';' in content
    
    def test_save_utf8_encoding(self, tmp_path):
        """
        Критичный тест: UTF-8 с BOM кодировка для кириллицы в Excel.
        
        Баг: CSV с некорректной кодировкой для русских символов.
        """
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        service._df = pd.DataFrame([{
            'item_name': 'Бревна сосны IV',
            'sell_price': 100,
            'buy_price': 150,
            'average_price': 125,
            'screenshot_date': '2026-06-11',
            'item_tier': 4,
            'item_enchantment': 0,
            'item_quality': 0
        }])
        service._save_data()
        
        # Проверить наличие BOM (первые 3 байта)
        with open(csv_file, 'rb') as f:
            bom = f.read(3)
            assert bom == b'\xef\xbb\xbf', "Файл должен начинаться с UTF-8 BOM для Excel"
        
        # Прочитать с UTF-8-sig и проверить кириллицу
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            assert 'Бревна сосны IV' in content
            # Разделитель точка с запятой
            assert ';' in content
    
    def test_save_line_terminator(self, tmp_path):
        """Проверка переводов строк (LF, не CRLF)."""
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        service._df = pd.DataFrame([{
            'item_name': 'Лен',
            'sell_price': 50,
            'buy_price': 55,
            'average_price': 52,
            'screenshot_date': '2026-06-11',
            'item_tier': 3,
            'item_enchantment': 0,
            'item_quality': 0
        }])
        service._save_data()
        
        with open(csv_file, 'rb') as f:
            content = f.read()
            # Должен быть \n, не \r\n
            assert b'\r\n' not in content
            assert b'\n' in content


class TestDataStorageService:
    """Тесты основного функционала DataStorageService."""
    
    def test_init_creates_empty_dataframe(self, tmp_path):
        """Инициализация создаёт пустой DataFrame."""
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        
        assert len(service._df) == 0
        assert list(service._df.columns) == CSV_COLUMNS
    
    def test_load_existing_data(self, tmp_path):
        """Загрузка существующих данных из CSV."""
        csv_file = tmp_path / "test.csv"
        
        # Создать тестовый CSV в Excel-формате (UTF-8 с BOM, разделитель ;)
        df = pd.DataFrame([{
            'item_name': 'Лен',
            'sell_price': 50,
            'buy_price': 55,
            'average_price': 52,
            'screenshot_date': '2026-06-11',
            'item_tier': 3,
            'item_enchantment': 0,
            'item_quality': 0
        }])
        df.to_csv(csv_file, index=False, encoding='utf-8-sig', sep=';')
        
        # Загрузить
        service = DataStorageService(data_file=csv_file)
        
        assert len(service._df) == 1
        assert service._df.iloc[0]['item_name'] == 'Лен'
    
    def test_get_all_items_empty(self, tmp_path):
        """Получение всех предметов из пустого хранилища."""
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        
        items = service.get_all_items()
        
        assert items == []
    
    def test_get_items_by_name(self, tmp_path):
        """Поиск предметов по названию."""
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        service._df = pd.DataFrame([
            {
                'item_name': 'Бревна сосны',
                'sell_price': 100,
                'buy_price': 150,
                'average_price': 125,
                'screenshot_date': '2026-06-11',
                'item_tier': 4,
                'item_enchantment': 0,
                'item_quality': 0
            },
            {
                'item_name': 'Бревна березы',
                'sell_price': 80,
                'buy_price': 120,
                'average_price': 100,
                'screenshot_date': '2026-06-11',
                'item_tier': 3,
                'item_enchantment': 0,
                'item_quality': 0
            }
        ])
        
        items = service.get_items_by_name('бревна сосны')
        
        assert len(items) == 1
        assert items[0]['item_name'] == 'Бревна сосны'
    
    def test_clear_data(self, tmp_path):
        """Очистка всех данных."""
        csv_file = tmp_path / "test.csv"
        service = DataStorageService(data_file=csv_file)
        service._df = pd.DataFrame([
            {
                'item_name': 'Бревна сосны',
                'sell_price': 100,
                'buy_price': 150,
                'average_price': 125,
                'screenshot_date': '2026-06-11',
                'item_tier': 4,
                'item_enchantment': 0,
                'item_quality': 0
            }
        ])
        
        service.clear_data()
        
        assert len(service._df) == 0
        assert csv_file.exists()  # Файл должен существовать, но пустой
