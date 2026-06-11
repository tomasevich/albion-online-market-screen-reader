"""Script to process and clean items.json catalog."""
import json
import logging
import re
from pathlib import Path

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


def parse_item_tier(unique_name: str) -> int:
    """
    Extract item tier from UniqueName.
    
    Examples:
        T6_MAIN_AXE@1 -> 6
        T4_BOW -> 4
        MAIN_SWORD -> 0
    """
    match = re.search(r"T(\d+)_?", unique_name)
    if match:
        return int(match.group(1))
    return 0


def parse_item_enchantment(unique_name: str) -> int:
    """
    Extract item enchantment from UniqueName.
    
    Examples:
        T6_MAIN_AXE@1 -> 1
        T4_BOW -> 0
        T8_OFFHAND_BOOK@3 -> 3
        T7_HIDE_LEVEL4@4 -> 4
    """
    match = re.search(r"@(\d+)$", unique_name)
    if match:
        return int(match.group(1))
    return 0


def process_items_catalog(input_path: Path, output_path: Path) -> None:
    """
    Process items.json catalog:
    - Keep only EN-US and RU-RU localizations
    - Add ItemTier, ItemEnchantment, ItemQuality fields
    """
    logger.info(f"Загрузка предметов из {input_path}...")
    
    with open(input_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    logger.info(f"Найдено {len(items)} предметов")
    
    processed_items = []
    
    for item in items:
        unique_name = item.get("UniqueName", "")
        localized_names = item.get("LocalizedNames")
        
        # Skip items with no LocalizedNames
        if not localized_names:
            continue
        
        # Keep only EN-US and RU-RU
        en_name = localized_names.get("EN-US", "")
        ru_name = localized_names.get("RU-RU", "")
        
        # Skip items without both names
        if not en_name or not ru_name:
            continue
        
        # Parse tier and enchantment
        item_tier = parse_item_tier(unique_name)
        item_enchantment = parse_item_enchantment(unique_name)
        item_quality = 0  # Default quality
        
        processed_item = {
            "UniqueName": unique_name,
            "LocalizedNames": {
                "EN-US": en_name,
                "RU-RU": ru_name
            },
            "ItemTier": item_tier,
            "ItemEnchantment": item_enchantment,
            "ItemQuality": item_quality
        }
        
        processed_items.append(processed_item)
    
    # Save processed catalog
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_items, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Обработано {len(processed_items)} предметов")
    logger.info(f"Сохранено в {output_path}")


def main():
    """Main entry point."""
    # Paths relative to script location
    script_dir = Path(__file__).parent.parent
    input_file = script_dir / "items.json"
    output_file = script_dir / "items.json"  # Overwrite original
    
    if not input_file.exists():
        logger.error(f"Файл не найден: {input_file}")
        return
    
    process_items_catalog(input_file, output_file)
    logger.info("Готово!")


if __name__ == "__main__":
    main()
