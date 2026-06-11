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
from src.utils.cleanup import cleanup_screenshots

# Настроить централизованное логирование
setup_logging()
logger = get_logger(__name__)


def clear_screen() -> None:
    """Очистить экран консоли."""
    os.system("cls" if os.name == "nt" else "clear")


def draw_menu(options: list, selected: int) -> None:
    """Отрисовать меню с выделением выбранного пункта."""
    print("\n╔═══════════════════════════════════════════════╗")
    print("║    Albion Online Market Screen Reader         ║")
    print("╠═══════════════════════════════════════════════╣")
    
    for i, option in enumerate(options):
        if i == selected:
            print(f"║  → {option:<39}    ║")
        else:
            print(f"║    {option:<39}    ║")
    
    print("╚═══════════════════════════════════════════════╝")
    print("\nСтрелки: выбор | Enter: начать | Esc: выход")


def handle_process_catalog() -> None:
    """Обработать пункт 1: Обработка справочника."""
    clear_screen()
    logger.info("Запуск обработки справочника предметов...")
    
    script_path = project_root / "scripts" / "process_items_catalog.py"
    
    if not script_path.exists():
        logger.error(f"Скрипт не найден: {script_path}")
        print(f"❌ Скрипт не найден: {script_path}")
        print("\nНажмите любую клавишу для возврата в меню...")
        try:
            readchar.readkey()
        except KeyboardInterrupt:
            pass
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
            logger.info("Справочник обработан успешно")
            print("\n✓ Справочник обработан успешно")
        else:
            logger.error("Ошибка при обработке справочника")
            print("\n❌ Ошибка при обработке справочника")
    except Exception as e:
        logger.exception(f"Ошибка при обработке справочника: {e}")
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    try:
        readchar.readkey()
    except KeyboardInterrupt:
        pass


def handle_calibration() -> None:
    """Обработать пункт 2: Калибровка изображения."""
    clear_screen()
    logger.info("Запуск инструмента калибровки...")
    print("Запуск инструмента калибровки...\n")
    
    script_path = project_root / "scripts" / "calibration_tool.py"
    
    if not script_path.exists():
        logger.error(f"Скрипт не найден: {script_path}")
        print(f"❌ Скрипт не найден: {script_path}")
        print("\nНажмите любую клавишу для возврата в меню...")
        try:
            readchar.readkey()
        except KeyboardInterrupt:
            pass
        return
    
    if not config.EXAMPLE_FILE.exists():
        logger.error(f"Файл примера не найден: {config.EXAMPLE_FILE}")
        print(f"❌ Файл примера не найден: {config.EXAMPLE_FILE}")
        print("\nНажмите любую клавишу для возврата в меню...")
        try:
            readchar.readkey()
        except KeyboardInterrupt:
            pass
        return
    
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            env=env
        )
        logger.info("Калибровка завершена")
        print("\n✓ Калибровка сохранена")
    except Exception as e:
        logger.exception(f"Ошибка при калибровке: {e}")
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    try:
        readchar.readkey()
    except KeyboardInterrupt:
        pass


def handle_set_hotkey() -> None:
    """Обработать пункт 3: Установка горячей клавиши."""
    clear_screen()
    logger.info("Начало установки горячей клавиши")
    print("Установка горячей клавиши\n")
    print("Нажмите желаемую комбинацию клавиш...")
    print("(или Esc для отмены)\n")
    
    try:
        # Ждать нажатия клавиши
        key = readchar.readkey()
        
        # Если нажат Esc — отмена
        if key == readchar.key.ESC:
            logger.info("Отмена установки горячей клавиши")
            print("\nОтменено.")
            print("\nНажмите любую клавишу для возврата в меню...")
            try:
                readchar.readkey()
            except KeyboardInterrupt:
                pass
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
        logger.info(f"Зафиксирована клавиша: {hotkey}")
        print(f"\n✓ Зафиксирована клавиша: {hotkey}")
        
        # Проверить возможность регистрации
        try:
            import keyboard
            keyboard.add_hotkey(hotkey, lambda: None)
            keyboard.remove_hotkey(hotkey)
            logger.info("Горячая клавиша валидирована успешно")
            print(f"✓ Горячая клавиша валидирована")
        except Exception as e:
            logger.warning(f"Валидация горячей клавиши не удалась: {e}")
            print(f"⚠ Предупреждение: {e}")
        
        # Сохранить в .env
        env_path = project_root / ".env"
        
        # Считать существующие переменные
        env_vars: dict = {}
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
        
        logger.info(f"Горячая клавиша установлена: {hotkey}")
        print(f"✓ Горячая клавиша установлена: {hotkey}")
        
    except Exception as e:
        logger.exception(f"Ошибка при установке горячей клавиши: {e}")
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    try:
        readchar.readkey()
    except KeyboardInterrupt:
        pass


def handle_monitoring() -> None:
    """Обработать пункт 4: Мониторинг экрана."""
    clear_screen()
    logger.info("Запуск мониторинга экрана...")
    print("Запуск мониторинга экрана...\n")
    print("Нажмите Ctrl+C для остановки\n")
    
    src_main_path = project_root / "src" / "main.py"
    
    if not src_main_path.exists():
        logger.error(f"Файл не найден: {src_main_path}")
        print(f"❌ Файл не найден: {src_main_path}")
        print("\nНажмите любую клавишу для возврата в меню...")
        try:
            readchar.readkey()
        except KeyboardInterrupt:
            pass
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
        
        logger.info("Мониторинг остановлен")
        print("\n✓ Мониторинг остановлен")
        
    except KeyboardInterrupt:
        logger.info("Мониторинг прерван пользователем")
        print("\n\n✓ Мониторинг остановлен")
    except Exception as e:
        logger.exception(f"Ошибка при мониторинге: {e}")
        print(f"\n❌ Ошибка: {e}")
    
    print("\nНажмите любую клавишу для возврата в меню...")
    try:
        readchar.readkey()
    except KeyboardInterrupt:
        pass


def main_menu() -> None:
    """Показать главное меню и обработать выбор."""
    options = [
        "Обработка справочника (item.json)",
        "Калибровка изображения (example.png)",
        "Установка горячей клавиши",
        "Мониторинг экрана",
        "Выход"
    ]
    
    selected = 0
    
    try:
        while True:
            try:
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
                        logger.info("Приложение завершено пользователем")
                        print("До свидания!\n")
                        break
                elif key == readchar.key.ESC:
                    # Подтверждение выхода
                    clear_screen()
                    print("Вы уверены, что хотите выйти? (y/n)")
                    try:
                        confirm = readchar.readkey().lower()
                    except KeyboardInterrupt:
                        continue
                    if confirm == "y":
                        clear_screen()
                        logger.info("Приложение завершено пользователем")
                        print("До свидания!\n")
                        break
            except KeyboardInterrupt:
                # Выход при Ctrl+C в меню
                clear_screen()
                logger.info("Приложение завершено пользователем (Ctrl+C)")
                print("До свидания!\n")
                break
    finally:
        # Очистить скриншоты при ЛЮБОМ выходе из меню
        cleanup_screenshots()


def main() -> None:
    """Точка входа программы."""
    logger.info("Запуск Albion Online Market Screen Reader...")
    main_menu()


if __name__ == "__main__":
    main()
