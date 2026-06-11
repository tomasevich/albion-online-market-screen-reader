"""Service for storing and managing market data."""
import csv
import logging
from pathlib import Path

from src.config import config
from src.models import MarketItem
from src.services.items_catalog_service import ItemsCatalogService

logger = logging.getLogger(__name__)


class DataStorageService:
    """Service responsible for persisting market data to CSV."""

    def __init__(self, data_file: Path = None, catalog_service: ItemsCatalogService = None):
        """
        Initialize the data storage service.
        
        Args:
            data_file: Path to the CSV data file. Defaults to config.DATA_FILE.
            catalog_service: ItemsCatalogService instance for enriching items.
        """
        self._data_file = data_file or config.DATA_FILE
        self._catalog_service = catalog_service
        self._data = self._load_data()

    def _load_data(self) -> list:
        """
        Load existing data from CSV file.
        
        Returns:
            List of market items, or empty list if file doesn't exist.
        """
        if not self._data_file.exists():
            logger.info(f"Data file not found, creating new: {self._data_file}")
            return []
        
        try:
            with open(self._data_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                data = list(reader)
                logger.info(f"Loaded {len(data)} items from data file")
                return data
        except (csv.Error, IOError) as e:
            logger.warning(f"Error loading data file: {e}, starting fresh")
            return []

    def _save_data(self) -> None:
        """Save current data to CSV file."""
        try:
            if not self._data:
                # Write empty file with headers
                with open(self._data_file, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        "item_name", "sell_price", "buy_price", "average_price", 
                        "screenshot_date", "item_tier", "item_enchantment", "item_quality"
                    ])
                    writer.writeheader()
            else:
                with open(self._data_file, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        "item_name", "sell_price", "buy_price", "average_price", 
                        "screenshot_date", "item_tier", "item_enchantment", "item_quality"
                    ])
                    writer.writeheader()
                    writer.writerows(self._data)
            logger.debug(f"Data saved to {self._data_file}")
        except IOError as e:
            logger.error(f"Error saving data: {e}")
            raise

    def add_item(self, item: MarketItem) -> None:
        """
        Add a new market item to the data store.
        Enriches item with catalog data if available.
        
        Args:
            item: MarketItem to add.
        """
        # Enrich item with catalog data if service is available
        if self._catalog_service:
            enrichment = self._catalog_service.enrich_item(item.item_name)
            item.item_tier = enrichment["item_tier"]
            item.item_enchantment = enrichment["item_enchantment"]
            item.item_quality = enrichment["item_quality"]
        
        self._data.append(item.to_dict())
        self._save_data()
        logger.info(f"Added item: {item.item_name} (tier={item.item_tier}, enchantment={item.item_enchantment})")

    def get_all_items(self) -> list:
        """
        Get all stored market items.
        
        Returns:
            List of all market items as dictionaries.
        """
        return self._data.copy()

    def get_items_by_name(self, item_name: str) -> list:
        """
        Get all items with the specified name.
        
        Args:
            item_name: Name of the item to search for.
            
        Returns:
            List of matching items.
        """
        return [
            item for item in self._data 
            if item.get("item_name", "").lower() == item_name.lower()
        ]

    def clear_data(self) -> None:
        """Clear all stored data."""
        self._data = []
        self._save_data()
        logger.info("All data cleared")
