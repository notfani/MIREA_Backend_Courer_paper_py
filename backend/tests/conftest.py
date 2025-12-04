import os
import sys
from unittest.mock import MagicMock, patch

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Устанавливаем переменные окружения перед импортом любых модулей
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["ENCRYPTION_KEY"] = "OdID4mXF1ogWAxjHuEy5ruu71SkEcmTa1ClCX2ymefw="
os.environ["REDIS_URL"] = "redis://localhost:6379"

# Мокируем подключение к базе данных при импорте
mock_connection = MagicMock()

# Применяем патч перед импортом database
sys.modules['database_patch'] = MagicMock()

def pytest_configure(config):
    """Конфигурация pytest перед запуском тестов"""
    pass

def pytest_sessionstart(session):
    """Вызывается перед началом тестовой сессии"""
    print("\n🧪 Запуск тестов...")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")
    print(f"ENCRYPTION_KEY установлен: {'да' if os.environ.get('ENCRYPTION_KEY') else 'нет'}")

