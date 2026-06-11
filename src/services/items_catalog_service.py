"""Сервис для управления каталогом предметов и обогащения рыночных данных."""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from thefuzz import fuzz

from src.config import config
from src.logging_config import get_logger

logger = get_logger(__name__)


# Порог совпадения для нечёткого поиска (0-100)
FUZZY_MATCH_THRESHOLD = 60  # Понижен для учёта OCR-ошибок


# Таблица замены визуально похожих латинских символов на кириллические
LATIN_TO_CYRILLIC = {
    'C': 'С',  # Latin C -> Cyrillic С
    'c': 'с',  # Latin c -> Cyrillic с
    'O': 'О',  # Latin O -> Cyrillic О
    'o': 'о',  # Latin o -> Cyrillic о
    'B': 'В',  # Latin B -> Cyrillic В
    'b': 'ь',  # Latin b -> Cyrillic ь (мягкий знак)
    'E': 'Е',  # Latin E -> Cyrillic Е
    'e': 'е',  # Latin e -> Cyrillic е
    'H': 'Н',  # Latin H -> Cyrillic Н
    'h': 'н',  # Latin h -> Cyrillic н
    'y': 'у',  # Latin y -> Cyrillic у
    'x': 'х',  # Latin x -> Cyrillic х
    'X': 'Х',  # Latin X -> Cyrillic Х
    'I': 'І',  # Latin I -> Cyrillic І
    'i': 'і',  # Latin i -> Cyrillic і
    'a': 'а',  # Latin a -> Cyrillic а
    'A': 'А',  # Latin A -> Cyrillic А
    'p': 'р',  # Latin p -> Cyrillic р
    'P': 'Р',  # Latin P -> Cyrillic Р
    'K': 'К',  # Latin K -> Cyrillic К
    'k': 'к',  # Latin k -> Cyrillic к
    'M': 'М',  # Latin M -> Cyrillic М
    'm': 'м',  # Latin m -> Cyrillic м
    'T': 'Т',  # Latin T -> Cyrillic Т
    't': 'т',  # Latin t -> Cyrillic т
    'Y': 'У',  # Latin Y -> Cyrillic У
    'r': 'г',  # Latin r -> Cyrillic г (иногда)
    's': 'з',  # Latin s -> Cyrillic з (иногда)
    'l': 'л',  # Latin l -> Cyrillic л
    'L': 'Л',  # Latin L -> Cyrillic Л
    'j': 'ј',  # Latin j -> Cyrillic ј
    'J': 'Ј',  # Latin J -> Cyrillic Ј
    'w': 'ш',  # Latin w -> Cyrillic ш (визуально)
    'W': 'Ш',  # Latin W -> Cyrillic Ш
    'g': 'д',  # Latin g -> Cyrillic д (иногда)
}


# Невидимые символы и артефакты для удаления
INVISIBLE_CHARS_PATTERN = re.compile(r'^[\u2000-\u206F\u0000-\u001F\u00A0\u200B\uFEFF‚]+')


class ItemsCatalogService:
    """Сервис для загрузки и поиска по каталогу предметов."""
    
    def __init__(self, catalog_path: Path = None):
        """
        Инициализировать сервис каталога предметов.
        
        Args:
            catalog_path: Путь к файлу каталога items.json. По умолчанию config.BASE_DIR/items.json.
        """
        self._catalog_path = catalog_path or (config.BASE_DIR / "items.json")
        self._items_by_name: dict = {}
        self._load_catalog()
    
    def _load_catalog(self) -> None:
        """Загрузить каталог предметов и построить индекс по названию."""
        if not self._catalog_path.exists():
            logger.warning(f"Каталог предметов не найден: {self._catalog_path}")
            return
        
        try:
            with open(self._catalog_path, "r", encoding="utf-8") as f:
                items = json.load(f)
            
            # Построить индекс по английскому и русскому названиям
            for item in items:
                localized_names = item.get("LocalizedNames")
                
                # Пропустить предметы без LocalizedNames
                if not localized_names:
                    continue
                
                # Индекс по русскому названию
                ru_name = localized_names.get("RU-RU", "")
                if ru_name:
                    self._items_by_name[ru_name.lower()] = item
                
                # Индекс по английскому названию
                en_name = localized_names.get("EN-US", "")
                if en_name:
                    self._items_by_name[en_name.lower()] = item
            
            logger.info(f"Загружено {len(self._items_by_name)} названий предметов из каталога")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Ошибка загрузки каталога предметов: {e}")
    
    def enrich_item(self, item_name: str) -> dict:
        """
        Обогатить название предмета данными о tier, enchantment и quality.
        
        Args:
            item_name: Название предмета (на русском или английском).
            
        Returns:
            Словарь с item_tier, item_enchantment, item_quality.
        """
        # Очистить название от артефактов и невидимых символов
        cleaned_name = self._clean_text(item_name)
        
        # Транслитерировать латиницу в кириллицу (для OCR-ошибок)
        transliterated_name = self._transliterate_latin_to_cyrillic(cleaned_name)
        
        # Нормализовать название: убрать лишние пробелы и привести к нижнему регистру
        normalized_name = transliterated_name.strip().lower()
        
        logger.debug(f"Очистка: '{item_name}' -> '{cleaned_name}' -> '{transliterated_name}' -> '{normalized_name}'")
        
        # Попробовать найти в каталоге по полному совпадению
        item_data = self._items_by_name.get(normalized_name)
        
        if item_data:
            logger.debug(f"Предмет '{item_name}' найден в каталоге (полное совпадение)")
            return {
                "item_tier": item_data.get("ItemTier", 0),
                "item_enchantment": item_data.get("ItemEnchantment", 0),
                "item_quality": item_data.get("ItemQuality", 0),
                "unique_name": item_data.get("UniqueName", ""),
            }
        
        # Попытка частичного поиска по подстроке
        item_data = self._partial_search(normalized_name)
        
        if item_data:
            logger.debug(f"Предмет '{item_name}' найден частичным поиском")
            return {
                "item_tier": item_data.get("ItemTier", 0),
                "item_enchantment": item_data.get("ItemEnchantment", 0),
                "item_quality": item_data.get("ItemQuality", 0),
                "unique_name": item_data.get("UniqueName", ""),
            }
        
        # Попытка нечёткого поиска (fuzzy search)
        item_data = self._fuzzy_search(normalized_name)
        
        if item_data:
            logger.debug(f"Предмет '{item_name}' найден нечётким поиском")
            return {
                "item_tier": item_data.get("ItemTier", 0),
                "item_enchantment": item_data.get("ItemEnchantment", 0),
                "item_quality": item_data.get("ItemQuality", 0),
                "unique_name": item_data.get("UniqueName", ""),
            }
        
        # Резервный метод: попытаться распарсить tier и enchantment из названия предмета
        # Это обрабатывает случаи когда OCR может включать tier в название
        tier = self._extract_tier_from_name(item_name)
        enchantment = self._extract_enchantment_from_name(item_name)
        
        logger.debug(f"Предмет '{item_name}' не найден в каталоге, используются распарсенные значения: tier={tier}, enchantment={enchantment}")
        
        return {
            "item_tier": tier,
            "item_enchantment": enchantment,
            "item_quality": 0,
            "unique_name": "",
        }
    
    def _clean_text(self, text: str) -> str:
        """
        Очистить текст от невидимых символов и артефактов кодировки.
        
        Args:
            text: Исходный текст.
            
        Returns:
            Очищенный текст.
        """
        # Удалить невидимые символы в начале строки
        cleaned = INVISIBLE_CHARS_PATTERN.sub('', text)
        # Удалить лишние пробелы
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    def _transliterate_latin_to_cyrillic(self, text: str) -> str:
        """
        Заменить визуально похожие латинские символы на кириллические.
        
        Args:
            text: Текст с возможными латинскими символами.
            
        Returns:
            Текст с заменёнными символами.
        """
        result = []
        changed = False
        
        for char in text:
            if char in LATIN_TO_CYRILLIC:
                result.append(LATIN_TO_CYRILLIC[char])
                changed = True
            else:
                result.append(char)
        
        if changed:
            logger.debug(f"Транслитерация: '{text}' -> {''.join(result)}'")
        
        return ''.join(result)
    
    def _partial_search(self, normalized_name: str) -> Optional[dict]:
        """
        Выполнить частичный поиск предмета по подстроке.
        
        Args:
            normalized_name: Нормализованное название предмета.
            
        Returns:
            Данные предмета или None если не найден.
        """
        # Убрать распространённые префиксы/суффиксы для поиска
        clean_name = normalized_name
        
        # Убрать слова-модификаторы
        modifiers = ["уникальная", "редкая", "необычная", "первозданная", 
                     "тяжелая", "прочная", "грубая", "тонкая", "средняя", "рваная"]
        
        for modifier in modifiers:
            clean_name = clean_name.replace(modifier, "").strip()
        
        # Искать совпадение по очищенному названию
        for name, item_data in self._items_by_name.items():
            # Проверить содержится ли очищенное название в ключах каталога
            if clean_name and len(clean_name) > 3:
                if clean_name in name or name in clean_name:
                    logger.debug(f"Частичное совпадение: '{clean_name}' -> '{name}'")
                    return item_data
        
        return None
    
    def _fuzzy_search(self, normalized_name: str) -> Optional[dict]:
        """
        Выполнить нечёткий поиск предмета с помощью алгоритма Левенштейна.
        
        Args:
            normalized_name: Нормализованное название предмета.
            
        Returns:
            Данные предмета или None если совпадение не найдено.
        """
        best_match = None
        best_score = 0
        
        # Убрать модификаторы для нечёткого поиска
        clean_name = normalized_name
        modifiers = ["уникальная", "редкая", "необычная", "первозданная", 
                     "тяжелая", "прочная", "грубая", "тонкая", "средняя", "рваная"]
        
        for modifier in modifiers:
            clean_name = clean_name.replace(modifier, "").strip()
        
        # Искать лучшее нечёткое совпадение
        for name, item_data in self._items_by_name.items():
            # Рассчитать коэффициент схожести (обычный)
            score = fuzz.ratio(clean_name, name)
            
            # Также проверить частичное соотношение (для случаев когда одно название короче)
            partial_score = fuzz.partial_ratio(clean_name, name)
            
            # Использовать token_sort_ratio для игнорирования порядка слов
            token_sort_score = fuzz.token_sort_ratio(clean_name, name)
            
            # Использовать максимальный из всех показателей
            final_score = max(score, partial_score, token_sort_score)
            
            if final_score > best_score and final_score >= FUZZY_MATCH_THRESHOLD:
                best_score = final_score
                best_match = item_data
        
        if best_match:
            logger.debug(f"Нечёткое совпадение: '{clean_name}' -> score={best_score}")
            return best_match
        
        return None
    
    def _extract_tier_from_name(self, item_name: str) -> int:
        """
        Извлечь tier из названия предмета (резервный метод).
        
        Examples:
            "T6 Battleaxe" -> 6
            "Tier 4 Bow" -> 4
            "4 тир" -> 4
        """
        # Искать паттерны типа "T6", "Tier 6", "4 тир" и т.д.
        match = re.search(r"T(\d+)|Tier\s*(\d+)|(\d+)\s*тир", item_name, re.IGNORECASE)
        if match:
            return int(match.group(1) or match.group(2) or match.group(3))
        return 0
    
    def _extract_enchantment_from_name(self, item_name: str) -> int:
        """
        Извлечь enchantment из названия предмета (резервный метод).
        
        Examples:
            "Battleaxe @1" -> 1
            "Enchanted @3" -> 3
            "+3" -> 3
        """
        # Искать паттерн @1, @2, @3, @4
        match = re.search(r"@(\d+)", item_name)
        if match:
            return int(match.group(1))
        
        # Искать паттерн +1, +2, +3, +4
        match = re.search(r"\+(\d+)", item_name)
        if match:
            return int(match.group(1))
        
        return 0
    
    def get_item_info(self, item_name: str) -> Optional[dict]:
        """
        Получить полную информацию о предмете из каталога.
        
        Args:
            item_name: Название предмета.
            
        Returns:
            Полные данные предмета или None если не найден.
        """
        return self._items_by_name.get(item_name.lower())
    
    def reload_catalog(self) -> None:
        """Перезагрузить каталог из файла (полезно для динамических обновлений)."""
        self._items_by_name.clear()
        self._load_catalog()
