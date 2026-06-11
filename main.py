#!/usr/bin/env python3
"""Единая точка входа в программу."""
import os
import subprocess
import sys
from pathlib import Path

import readchar

# Добавить корень проекта в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.logging_config import setup_logging, get_logger

# Настроить централизованное логирование
setup_logging()
logger = get_logger(__name__)


def clear_screen():
    """Очистить экран консоли."""
    os.system("cls" if os.name == "nt" else "clear")


def draw_menu(options: list, selected: int):
    """Отрисовать меню с выделением выбранного пункта."""
    print("\n╔═══════════════════════════════════════════════╗")
    print("║    Screen Market Scraper — Главное меню       ║")
    print("╠═══════════════════════════════════════════════╣")
    
    for i, option in enumerate(options):
        if i == selected:
            print(f"║  → {option:<39} ║")
        else:
            print(f"║    {option:<39} ║")
    
    print("╚═══════════════════════════════════════════════╝")
    print("\nСтрелки: выбор | Enter: начать | Esc: выход")


def handle_process_catalog():
    """Обработать пункт 1: Обработка справочника."""
    clear_screen()
    print("Обработка справочника предметов...\n")
    
    script_path = project_root / "scripts" / "process_items_catalog.py"
    
    if not script_path.exists():
        print(f"❌ Скрипт не найден: {script_path}")
        print("\nНажмите любую клавишу для возврата в меню...")
        readchar.readkey()
        return
    
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=False,
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            print("\n✓ Справочник обработан успешно")
        else:
            print("\n❌ Ошибка при обработке справочника")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    readchar.readkey()


def handle_calibration():
    """Обработать пункт 2: Калибровка изображения."""
    clear_screen()
    print("Запуск инструмента калибровки...\n")
    
    script_path = project_root / "scripts" / "calibration_tool.py"
    
    if not script_path.exists():
        print(f"❌ Скрипт не найден: {script_path}")
        print("\nНажмите любую клавишу для возврата в меню...")
        readchar.readkey()
        return
    
    if not config.EXAMPLE_FILE.exists():
        print(f"❌ Файл примера не найден: {config.EXAMPLE_FILE}")
        print("\nНажмите любую клавишу для возврата в меню...")
        readchar.readkey()
        return
    
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            env=env
        )
        print("\n✓ Калибровка сохранена")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    readchar.readkey()


def handle_set_hotkey():
    """Обработать пункт 3: Установка горячей клавиши."""
    clear_screen()
    print("Установка горячей клавиши\n")
    print("Нажмите желаемую комбинацию клавиш...")
    print("(или Esc для отмены)\n")
    
    try:
        # Ждать нажатия клавиши
        key = readchar.readkey()
        
        # Если нажат Esc — отмена
        if key == readchar.key.ESC:
            print("\nОтменено.")
            print("\nНажмите любую клавишу для возврата в меню...")
            readchar.readkey()
            return
        
        # Обработать специальные клавиши
        if key == readchar.key.UP:
            hotkey = "up"
        elif key == readchar.key.DOWN:
            hotkey = "down"
        elif key == readchar.key.LEFT:
            hotkey = "left"
        elif key == readchar.key.RIGHT:
            hotkey = "right"
        elif key == readchar.key.ENTER:
            hotkey = "enter"
        elif key == readchar.key.SPACE:
            hotkey = "space"
        elif key == readchar.key.ESC:
            hotkey = "esc"
        elif key == readchar.key.BACKSPACE:
            hotkey = "backspace"
        elif key == readchar.key.TAB:
            hotkey = "tab"
        elif key == readchar.key.CTRL:
            hotkey = "ctrl"
        elif key == readchar.key.ALT:
            hotkey = "alt"
        elif key == readchar.key.SHIFT:
            hotkey = "shift"
        else:
            hotkey = key.lower()
        
        # Вывести результат
        print(f"\n✓ Зафиксирована клавиша: {hotkey}")
        
        # Проверить возможность регистрации
        try:
            import keyboard
            keyboard.add_hotkey(hotkey, lambda: None)
            keyboard.remove_hotkey(hotkey)
            print(f"✓ Горячая клавиша валидирована")
        except Exception as e:
            print(f"⚠ Предупреждение: {e}")
        
        # Сохранить в .env
        env_path = project_root / ".env"
        
        # Считать существующие переменные
        env_vars = {}
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key_name, value = line.split("=", 1)
                        env_vars[key_name.strip()] = value.strip()
        
        # Обновить HOTKEY
        env_vars["HOTKEY"] = hotkey
        
        # Записать обратно
        with open(env_path, "w", encoding="utf-8") as f:
            for key_name, value in env_vars.items():
                f.write(f"{key_name}={value}\n")
        
        print(f"✓ Горячая клавиша установлена: {hotkey}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    readchar.readkey()


def handle_monitoring():
    """Обработать пункт 4: Мониторинг экрана."""
    clear_screen()
    print("Запуск мониторинга экрана...\n")
    print("Нажмите Ctrl+C для остановки\n")
    
    src_main_path = project_root / "src" / "main.py"
    
    if not src_main_path.exists():
        print(f"❌ Файл не найден: {src_main_path}")
        print("\nНажмите любую клавишу для возврата в меню...")
        readchar.readkey()
        return
    
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        
        # Запустить мониторинг
        subprocess.run(
            [sys.executable, str(src_main_path)],
            cwd=project_root,
            env=env
        )
        
        print("\n✓ Мониторинг остановлен")
        
        # Очистить папку screenshots
        screenshots_dir = config.SCREENSHOTS_DIR
        if screenshots_dir.exists():
            count = 0
            for file in screenshots_dir.iterdir():
                if file.is_file():
                    file.unlink()
                    count += 1
            print(f"✓ Папка screenshots очищена ({count} файлов)")
        else:
            print("✓ Папка screenshots очищена")
            
    except KeyboardInterrupt:
        print("\n\n✓ Мониторинг остановлен")
        
        # Очистить папку screenshots
        screenshots_dir = config.SCREENSHOTS_DIR
        if screenshots_dir.exists():
            count = 0
            for file in screenshots_dir.iterdir():
                if file.is_file():
                    file.unlink()
                    count += 1
            print(f"✓ Папка screenshots очищена ({count} файлов)")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    readchar.readkey()


def main_menu():
    """Показать главное меню и обработать выбор."""
    options = [
        "Обработка справочника (item.json)",
        "Калибровка изображения (example.png)",
        "Установка горячей клавиши",
        "Мониторинг экрана",
        "Выход"
    ]
    
    selected = 0
    
    while True:
        clear_screen()
        draw_menu(options, selected)
        
        key = readchar.readkey()
        
        if key == readchar.key.UP:
            selected = (selected - 1) % len(options)
        elif key == readchar.key.DOWN:
            selected = (selected + 1) % len(options)
        elif key == readchar.key.ENTER:
            if selected == 0:
                handle_process_catalog()
            elif selected == 1:
                handle_calibration()
            elif selected == 2:
                handle_set_hotkey()
            elif selected == 3:
                handle_monitoring()
            elif selected == 4:
                # Выход
                clear_screen()
                print("До свидания!\n")
                break
        elif key == readchar.key.ESC:
            # Подтверждение выхода
            clear_screen()
            print("Вы уверены, что хотите выйти? (y/n)")
            confirm = readchar.readkey().lower()
            if confirm == "y":
                clear_screen()
                print("До свидания!\n")
                break


def main():
    """Точка входа программы."""
    main_menu()


if __name__ == "__main__":
    main()
