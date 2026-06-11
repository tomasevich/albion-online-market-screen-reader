"""Сервис для хранения и управления рыночными данными."""
import logging
from pathlib import Path

import pandas as pd

from src.config import config
from src.logging_config import get_logger
from src.models import MarketItem
from src.services.items_catalog_service import ItemsCatalogService

logger = get_logger(__name__)


# Поля CSV файла
CSV_COLUMNS = [
    "item_name", "sell_price", "buy_price", "average_price",
    "screenshot_date", "item_tier", "item_enchantment", "item_quality"
]


class DataStorageService:
    """Сервис для сохранения рыночных данных в CSV с использованием pandas."""

    def __init__(self, data_file: Path = None, catalog_service: ItemsCatalogService = None):
        """
        Инициализировать сервис хранения данных.
        
        Args:
            data_file: Путь к CSV файлу данных. По умолчанию config.DATA_FILE.
            catalog_service: Экземпляр ItemsCatalogService для обогащения предметов.
        """
        self._data_file = data_file or config.DATA_FILE
        self._catalog_service = catalog_service
        self._df: pd.DataFrame = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """
        Загрузить существующие данные из CSV файла.
        
        Returns:
            DataFrame с данными, или пустой DataFrame если файл не найден.
        """
        if not self._data_file.exists():
            logger.info(f"Файл данных не найден, создаю новый: {self._data_file}")
            return pd.DataFrame(columns=CSV_COLUMNS)
        
        try:
            df = pd.read_csv(
                self._data_file,
                encoding='utf-8',
                dtype={
                    'item_name': str,
                    'sell_price': int,
                    'buy_price': int,
                    'average_price': int,
                    'screenshot_date': str,
                    'item_tier': int,
                    'item_enchantment': int,
                    'item_quality': int
                }
            )
            logger.info(f"Загружено {len(df)} предметов из файла данных")
            return df
        except (pd.errors.EmptyDataError, pd.errors.ParserError, IOError) as e:
            logger.warning(f"Ошибка загрузки файла данных: {e}, начинаю заново")
            return pd.DataFrame(columns=CSV_COLUMNS)

    def _save_data(self) -> None:
        """Сохранить текущие данные в CSV файл с использованием pandas."""
        try:
            # Сохранить с явной кодировкой UTF-8 без BOM и форматом чисел
            self._df.to_csv(
                self._data_file,
                encoding='utf-8',
                index=False,
                quoting=1,  # QUOTE_MINIMAL
                lineterminator='\n',
                float_format='%.0f',  # Числа без десятичных
                na_rep='0'  # Заменить NaN на 0
            )
            logger.debug(f"Данные сохранены в {self._data_file} ({len(self._df)} записей)")
            
            # Логировать первую строку для диагностики формата
            if len(self._df) > 0:
                first_row = self._df.iloc[0].to_dict()
                logger.debug(f"Пример данных: item_name='{first_row.get('item_name', '')}', sell_price={first_row.get('sell_price', 0)}")
        except IOError as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            raise

    def add_item(self, item: MarketItem) -> None:
        """
        Добавить новый рыночный предмет в хранилище данных.
        Обогащает предмет данными из каталога если доступно.
        
        Args:
            item: MarketItem для добавления.
        """
        # Обогащать предмет данными из каталога если сервис доступен
        if self._catalog_service:
            enrichment = self._catalog_service.enrich_item(item.item_name)
            logger.debug(f"Обогащение для '{item.item_name}': tier={enrichment['item_tier']}, enchantment={enrichment['item_enchantment']}")
            item.item_tier = enrichment["item_tier"]
            item.item_enchantment = enrichment["item_enchantment"]
            item.item_quality = enrichment["item_quality"]
        
        # Создать новую строку данных с явными типами
        new_row = pd.DataFrame([{
            'item_name': str(item.item_name),
            'sell_price': int(item.sell_price),
            'buy_price': int(item.buy_price),
            'average_price': int(item.average_price),
            'screenshot_date': str(item.screenshot_date),
            'item_tier': int(item.item_tier),
            'item_enchantment': int(item.item_enchantment),
            'item_quality': int(item.item_quality)
        }], columns=CSV_COLUMNS)
        
        # Добавить к DataFrame
        self._df = pd.concat([self._df, new_row], ignore_index=True)
        
        # Привести типы данных к корректным
        self._convert_dtypes()
        
        # Сохранить
        self._save_data()
        
        logger.info(f"Добавлен предмет: {item.item_name} (tier={item.item_tier}, enchantment={item.item_enchantment})")

    def _convert_dtypes(self) -> None:
        """Привести типы данных DataFrame к корректным."""
        if len(self._df) == 0:
            return
        
        # Преобразовать числовые колонки к int (заполняя NaN нулями)
        numeric_cols = ['sell_price', 'buy_price', 'average_price', 'item_tier', 'item_enchantment', 'item_quality']
        for col in numeric_cols:
            self._df[col] = pd.to_numeric(self._df[col], errors='coerce').fillna(0).astype(int)

    def get_all_items(self) -> list:
        """
        Получить все сохранённые рыночные предметы.
        
        Returns:
            Список всех рыночных предметов как словари.
        """
        return self._df.to_dict('records') if len(self._df) > 0 else []

    def get_items_by_name(self, item_name: str) -> list:
        """
        Получить все предметы с указанным названием.
        
        Args:
            item_name: Название предмета для поиска.
            
        Returns:
            Список совпадающих предметов.
        """
        if len(self._df) == 0:
            return []
        
        mask = self._df['item_name'].str.lower() == item_name.lower()
        return self._df[mask].to_dict('records')

    def clear_data(self) -> None:
        """Очистить все сохранённые данные."""
        self._df = pd.DataFrame(columns=CSV_COLUMNS)
        self._save_data()
        logger.info("Все данные очищены")
