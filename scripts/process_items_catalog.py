"""Script to process and clean items.json catalog."""
import json
import re
from pathlib import Path


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
    """
    match = re.search(r"@@(\d+)", unique_name)
    if match:
        return int(match.group(1))
    return 0


def process_items_catalog(input_path: Path, output_path: Path) -> None:
    """
    Process items.json catalog:
    - Keep only EN-US and RU-RU localizations
    - Add ItemTier, ItemEnchantment, ItemQuality fields
    """
    print(f"Loading items from {input_path}...")
    
    with open(input_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    print(f"Found {len(items)} items")
    
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
    
    print(f"Processed {len(processed_items)} items")
    print(f"Saved to {output_path}")


def main():
    """Main entry point."""
    # Paths relative to script location
    script_dir = Path(__file__).parent.parent
    input_file = script_dir / "items.json"
    output_file = script_dir / "items.json"  # Overwrite original
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return
    
    process_items_catalog(input_file, output_file)
    print("Done!")


if __name__ == "__main__":
    main()
