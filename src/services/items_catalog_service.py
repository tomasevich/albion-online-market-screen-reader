"""Service for managing items catalog and enriching market data."""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from src.config import config

logger = logging.getLogger(__name__)


class ItemsCatalogService:
    """Service for loading and querying items catalog."""
    
    def __init__(self, catalog_path: Path = None):
        """
        Initialize the items catalog service.
        
        Args:
            catalog_path: Path to items.json catalog file. Defaults to config.BASE_DIR/items.json.
        """
        self._catalog_path = catalog_path or (config.BASE_DIR / "items.json")
        self._items_by_name: dict = {}
        self._load_catalog()
    
    def _load_catalog(self) -> None:
        """Load items catalog and build index by name."""
        if not self._catalog_path.exists():
            logger.warning(f"Items catalog not found: {self._catalog_path}")
            return
        
        try:
            with open(self._catalog_path, "r", encoding="utf-8") as f:
                items = json.load(f)
            
            # Build index by both English and Russian names
            for item in items:
                localized_names = item.get("LocalizedNames")
                
                # Skip items with no LocalizedNames
                if not localized_names:
                    continue
                
                # Index by Russian name
                ru_name = localized_names.get("RU-RU", "")
                if ru_name:
                    self._items_by_name[ru_name.lower()] = item
                
                # Index by English name
                en_name = localized_names.get("EN-US", "")
                if en_name:
                    self._items_by_name[en_name.lower()] = item
            
            logger.info(f"Loaded {len(self._items_by_name)} item names from catalog")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading items catalog: {e}")
    
    def enrich_item(self, item_name: str) -> dict:
        """
        Enrich item name with tier, enchantment, and quality data.
        
        Args:
            item_name: Name of the item (in Russian or English).
            
        Returns:
            Dictionary with item_tier, item_enchantment, item_quality.
        """
        # Try to find in catalog
        item_data = self._items_by_name.get(item_name.lower())
        
        if item_data:
            return {
                "item_tier": item_data.get("ItemTier", 0),
                "item_enchantment": item_data.get("ItemEnchantment", 0),
                "item_quality": item_data.get("ItemQuality", 0),
                "unique_name": item_data.get("UniqueName", ""),
            }
        
        # Fallback: try to parse tier and enchantment from item name itself
        # This handles cases where OCR might include tier in the name
        tier = self._extract_tier_from_name(item_name)
        enchantment = self._extract_enchantment_from_name(item_name)
        
        logger.debug(f"Item '{item_name}' not found in catalog, using parsed values: tier={tier}, enchantment={enchantment}")
        
        return {
            "item_tier": tier,
            "item_enchantment": enchantment,
            "item_quality": 0,
            "unique_name": "",
        }
    
    def _extract_tier_from_name(self, item_name: str) -> int:
        """
        Extract tier from item name (fallback method).
        
        Examples:
            "T6 Battleaxe" -> 6
            "Tier 4 Bow" -> 4
        """
        # Look for patterns like "T6", "Tier 6", etc.
        match = re.search(r"T(\d+)|Tier\s*(\d+)", item_name, re.IGNORECASE)
        if match:
            return int(match.group(1) or match.group(2))
        return 0
    
    def _extract_enchantment_from_name(self, item_name: str) -> int:
        """
        Extract enchantment from item name (fallback method).
        
        Examples:
            "Battleaxe @1" -> 1
            "Enchanted @3" -> 3
        """
        match = re.search(r"@@(\d+)", item_name)
        if match:
            return int(match.group(1))
        return 0
    
    def get_item_info(self, item_name: str) -> Optional[dict]:
        """
        Get full item information from catalog.
        
        Args:
            item_name: Name of the item.
            
        Returns:
            Full item data or None if not found.
        """
        return self._items_by_name.get(item_name.lower())
    
    def reload_catalog(self) -> None:
        """Reload catalog from file (useful for dynamic updates)."""
        self._items_by_name.clear()
        self._load_catalog()
