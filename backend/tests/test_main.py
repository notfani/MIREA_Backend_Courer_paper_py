import pytest
import os
import sys

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Устанавливаем переменные окружения ДО импорта модулей
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["ENCRYPTION_KEY"] = "OdID4mXF1ogWAxjHuEy5ruu71SkEcmTa1ClCX2ymefw="
os.environ["REDIS_URL"] = "redis://localhost:6379"

# Мокируем database.py, чтобы не пытался подключаться к PostgreSQL
from unittest.mock import MagicMock, patch

# Создаем мок для проверки подключения к БД
mock_connection = MagicMock()

with patch('database.engine.connect', return_value=mock_connection):
    # Теперь импортируем все остальное
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from main import app
    from database import Base

# Тестовая база данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Переопределение зависимости для тестирования"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Переопределяем зависимость get_db
from auth import get_db
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    """Фикстура для получения тестовой БД"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Фикстура для создания тестового пользователя"""
    response = client.post(
        "/register/",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    return {"username": "testuser", "password": "testpass123"}


@pytest.fixture
def auth_headers(test_user):
    """Фикстура для получения заголовков аутентификации"""
    response = client.post(
        "/token",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAuthentication:
    """Тесты аутентификации"""

    def test_register_user(self, test_db):
        """Тест регистрации пользователя"""
        response = client.post(
            "/register/",
            json={"username": "newuser", "password": "password123"}
        )
        assert response.status_code == 200
        assert "user_id" in response.json()

    def test_register_duplicate_user(self, test_user):
        """Тест регистрации существующего пользователя"""
        response = client.post(
            "/register/",
            json={"username": test_user["username"], "password": "password123"}
        )
        assert response.status_code == 400

    def test_register_short_username(self, test_db):
        """Тест регистрации с коротким именем пользователя"""
        response = client.post(
            "/register/",
            json={"username": "ab", "password": "password123"}
        )
        assert response.status_code == 422

    def test_register_short_password(self, test_db):
        """Тест регистрации с коротким паролем"""
        response = client.post(
            "/register/",
            json={"username": "testuser2", "password": "12345"}
        )
        assert response.status_code == 422

    def test_login_success(self, test_user):
        """Тест успешного входа"""
        response = client.post(
            "/token",
            data={"username": test_user["username"], "password": test_user["password"]}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, test_user):
        """Тест входа с неправильным паролем"""
        response = client.post(
            "/token",
            data={"username": test_user["username"], "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, test_db):
        """Тест входа несуществующего пользователя"""
        response = client.post(
            "/token",
            data={"username": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401


class TestChats:
    """Тесты работы с чатами"""

    def test_create_chat(self, auth_headers):
        """Тест создания чата"""
        response = client.post(
            "/chats/",
            json={"name": "Test Chat", "is_group": False},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Chat"

    def test_create_chat_unauthorized(self, test_db):
        """Тест создания чата без авторизации"""
        response = client.post(
            "/chats/",
            json={"name": "Test Chat", "is_group": False}
        )
        assert response.status_code == 401

    def test_get_user_chats(self, auth_headers):
        """Тест получения чатов пользователя"""
        # Создаем чат
        client.post(
            "/chats/",
            json={"name": "Test Chat", "is_group": False},
            headers=auth_headers
        )

        # Получаем список чатов
        response = client.get("/chats/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_get_chats_unauthorized(self, test_db):
        """Тест получения чатов без авторизации"""
        response = client.get("/chats/")
        assert response.status_code == 401


class TestMessages:
    """Тесты работы с сообщениями"""

    @pytest.fixture
    def test_chat(self, auth_headers):
        """Фикстура для создания тестового чата"""
        response = client.post(
            "/chats/",
            json={"name": "Test Chat", "is_group": False},
            headers=auth_headers
        )
        return response.json()

    def test_get_chat_messages(self, auth_headers, test_chat):
        """Тест получения сообщений чата"""
        chat_id = test_chat["id"]
        response = client.get(
            f"/chats/{chat_id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_messages_unauthorized(self, test_chat):
        """Тест получения сообщений без авторизации"""
        chat_id = test_chat["id"]
        response = client.get(f"/chats/{chat_id}/messages")
        assert response.status_code == 401

    def test_get_nonexistent_chat_messages(self, auth_headers):
        """Тест получения сообщений несуществующего чата"""
        response = client.get("/chats/99999/messages", headers=auth_headers)
        assert response.status_code == 404


class TestUsers:
    """Тесты работы с пользователями"""

    def test_get_all_users(self, auth_headers):
        """Тест получения всех пользователей"""
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    def test_get_users_unauthorized(self, test_db):
        """Тест получения пользователей без авторизации"""
        response = client.get("/users/")
        assert response.status_code == 401


class TestChatMembers:
    """Тесты управления участниками чата"""

    @pytest.fixture
    def test_chat(self, auth_headers):
        """Фикстура для создания тестового чата"""
        response = client.post(
            "/chats/",
            json={"name": "Test Chat", "is_group": True},
            headers=auth_headers
        )
        return response.json()

    @pytest.fixture
    def second_user(self, test_db):
        """Фикстура для создания второго пользователя"""
        response = client.post(
            "/register/",
            json={"username": "seconduser", "password": "password123"}
        )
        assert response.status_code == 200
        return {"username": "seconduser", "password": "password123"}

    def test_get_chat_members(self, auth_headers, test_chat):
        """Тест получения участников чата"""
        chat_id = test_chat["id"]
        response = client.get(
            f"/chats/{chat_id}/members",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_member_to_chat(self, auth_headers, test_chat, second_user):
        """Тест добавления участника в чат"""
        chat_id = test_chat["id"]
        response = client.post(
            f"/chats/{chat_id}/members",
            json={"username": second_user["username"]},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_remove_member_from_chat(self, auth_headers, test_chat, second_user):
        """Тест удаления участника из чата"""
        chat_id = test_chat["id"]

        # Сначала добавляем участника
        client.post(
            f"/chats/{chat_id}/members",
            json={"username": second_user["username"]},
            headers=auth_headers
        )

        # Затем удаляем
        response = client.delete(
            f"/chats/{chat_id}/members/{second_user['username']}",
            headers=auth_headers
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

