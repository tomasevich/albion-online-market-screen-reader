"""Тесты для утилиты очистки скриншотов."""
import pytest
from pathlib import Path
from unittest.mock import patch

from src.utils.cleanup import cleanup_screenshots


class TestCleanupScreenshots:
    """Тесты очистки папки скриншотов."""
    
    def test_cleanup_removes_all_files(self, tmp_path):
        """Удаление всех файлов из папки."""
        # Создать тестовые файлы
        (tmp_path / "screenshot1.png").touch()
        (tmp_path / "screenshot2.png").touch()
        (tmp_path / "debug_image.png").touch()
        (tmp_path / "test.txt").touch()
        (tmp_path / "data.csv").touch()
        
        # Патч конфига
        with patch('src.utils.cleanup.config') as mock_config:
            mock_config.SCREENSHOTS_DIR = tmp_path
            
            cleanup_screenshots()
        
        # Проверить что все файлы удалены
        assert not (tmp_path / "screenshot1.png").exists()
        assert not (tmp_path / "screenshot2.png").exists()
        assert not (tmp_path / "debug_image.png").exists()
        assert not (tmp_path / "test.txt").exists()
        assert not (tmp_path / "data.csv").exists()
    
    def test_cleanup_removes_subdirectories(self, tmp_path):
        """Удаление подпапок."""
        # Создать подпапку с файлами
        subdir = tmp_path / "subfolder"
        subdir.mkdir()
        (subdir / "file.png").touch()
        (subdir / "file.txt").touch()
        
        with patch('src.utils.cleanup.config') as mock_config:
            mock_config.SCREENSHOTS_DIR = tmp_path
            
            cleanup_screenshots()
        
        # Проверить что подпапка удалена
        assert not subdir.exists()
    
    def test_cleanup_empty_directory(self, tmp_path):
        """Очистка пустой папки."""
        with patch('src.utils.cleanup.config') as mock_config:
            mock_config.SCREENSHOTS_DIR = tmp_path
            
            # Не должно вызвать ошибок
            cleanup_screenshots()
        
        # Папка должна существовать
        assert tmp_path.exists()
    
    def test_cleanup_nonexistent_directory(self, tmp_path):
        """Очистка несуществующей папки."""
        nonexistent = tmp_path / "nonexistent"
        
        with patch('src.utils.cleanup.config') as mock_config:
            mock_config.SCREENSHOTS_DIR = nonexistent
            
            # Не должно вызвать ошибок
            cleanup_screenshots()
    
    def test_cleanup_mixed_content(self, tmp_path):
        """Очистка смешанного содержимого."""
        # Создать файлы и подпапки
        (tmp_path / "file1.png").touch()
        (tmp_path / "file2.jpg").touch()
        
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.png").touch()
        
        with patch('src.utils.cleanup.config') as mock_config:
            mock_config.SCREENSHOTS_DIR = tmp_path
            
            cleanup_screenshots()
        
        # Всё должно быть удалено
        assert len(list(tmp_path.iterdir())) == 0
    
    def test_cleanup_preserves_directory(self, tmp_path):
        """Папка сохраняется после очистки."""
        (tmp_path / "test.png").touch()
        
        with patch('src.utils.cleanup.config') as mock_config:
            mock_config.SCREENSHOTS_DIR = tmp_path
            
            cleanup_screenshots()
        
        # Папка должна существовать, но быть пустой
        assert tmp_path.exists()
        assert len(list(tmp_path.iterdir())) == 0
