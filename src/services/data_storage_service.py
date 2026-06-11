"""Сервис для хранения и управления рыночными данными."""
import csv
import logging
from pathlib import Path

from src.config import config
from src.logging_config import get_logger
from src.models import MarketItem
from src.services.items_catalog_service import ItemsCatalogService

logger = get_logger(__name__)


class DataStorageService:
    """Сервис для сохранения рыночных данных в CSV."""

    def __init__(self, data_file: Path = None, catalog_service: ItemsCatalogService = None):
        """
        Инициализировать сервис хранения данных.
        
        Args:
            data_file: Путь к CSV файлу данных. По умолчанию config.DATA_FILE.
            catalog_service: Экземпляр ItemsCatalogService для обогащения предметов.
        """
        self._data_file = data_file or config.DATA_FILE
        self._catalog_service = catalog_service
        self._data: list = self._load_data()

    def _load_data(self) -> list:
        """
        Загрузить существующие данные из CSV файла.
        
        Returns:
            Список рыночных предметов, или пустой список если файл не найден.
        """
        if not self._data_file.exists():
            logger.info(f"Файл данных не найден, создаю новый: {self._data_file}")
            return []
        
        try:
            with open(self._data_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = list(reader)
                logger.info(f"Загружено {len(data)} предметов из файла данных")
                return data
        except (csv.Error, IOError) as e:
            logger.warning(f"Ошибка загрузки файла данных: {e}, начинаю заново")
            return []

    def _save_data(self) -> None:
        """Сохранить текущие данные в CSV файл."""
        try:
            if not self._data:
                # Записать пустой файл с заголовками
                with open(self._data_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "item_name", "sell_price", "buy_price", "average_price",
                            "screenshot_date", "item_tier", "item_enchantment", "item_quality"
                        ],
                        quoting=csv.QUOTE_MINIMAL
                    )
                    writer.writeheader()
            else:
                with open(self._data_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "item_name", "sell_price", "buy_price", "average_price",
                            "screenshot_date", "item_tier", "item_enchantment", "item_quality"
                        ],
                        quoting=csv.QUOTE_MINIMAL
                    )
                    writer.writeheader()
                    writer.writerows(self._data)
            logger.debug(f"Данные сохранены в {self._data_file}")
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
            item.item_tier = enrichment["item_tier"]
            item.item_enchantment = enrichment["item_enchantment"]
            item.item_quality = enrichment["item_quality"]
        
        self._data.append(item.to_dict())
        self._save_data()
        logger.info(f"Добавлен предмет: {item.item_name} (tier={item.item_tier}, enchantment={item.item_enchantment})")

    def get_all_items(self) -> list:
        """
        Получить все сохранённые рыночные предметы.
        
        Returns:
            Список всех рыночных предметов как словари.
        """
        return self._data.copy()

    def get_items_by_name(self, item_name: str) -> list:
        """
        Получить все предметы с указанным названием.
        
        Args:
            item_name: Название предмета для поиска.
            
        Returns:
            Список совпадающих предметов.
        """
        return [
            item for item in self._data 
            if item.get("item_name", "").lower() == item_name.lower()
        ]

    def clear_data(self) -> None:
        """Очистить все сохранённые данные."""
        self._data = []
        self._save_data()
        logger.info("Все данные очищены")
