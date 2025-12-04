import pytest
import os
import sys

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Устанавливаем переменные окружения ДО импорта модулей
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["ENCRYPTION_KEY"] = "OdID4mXF1ogWAxjHuEy5ruu71SkEcmTa1ClCX2ymefw="

from auth import verify_password, get_password_hash, create_access_token, verify_token
from jose import jwt
from datetime import timedelta


class TestPasswordHashing:
    """Тесты хеширования паролей"""

    def test_hash_password(self):
        """Тест хеширования пароля"""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_correct_password(self):
        """Тест проверки правильного пароля"""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Тест проверки неправильного пароля"""
        password = "mysecretpassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_same_password_different_hashes(self):
        """Тест что одинаковые пароли дают разные хеши"""
        password = "mysecretpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Хеши должны отличаться из-за разных солей
        assert hash1 != hash2

        # Но оба должны верифицироваться
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWT:
    """Тесты работы с JWT токенами"""

    def test_create_access_token(self):
        """Тест создания токена доступа"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Тест проверки валидного токена"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "testuser"

    def test_verify_invalid_token(self):
        """Тест проверки невалидного токена"""
        invalid_token = "invalid.token.here"

        payload = verify_token(invalid_token)
        assert payload is None

    def test_token_expiration(self):
        """Тест истечения токена"""
        data = {"sub": "testuser"}
        # Создаем токен с очень коротким временем жизни
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        payload = verify_token(token)
        # Токен должен быть просрочен
        assert payload is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

