import pytest
import os
import sys

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Устанавливаем переменные окружения ДО импорта модулей
os.environ["ENCRYPTION_KEY"] = "OdID4mXF1ogWAxjHuEy5ruu71SkEcmTa1ClCX2ymefw="

from encryption import encrypt_message, decrypt_message


class TestEncryption:
    """Тесты шифрования сообщений"""

    def test_encrypt_decrypt_message(self):
        """Тест шифрования и дешифрования сообщения"""
        original_message = "Привет, мир!"
        encrypted = encrypt_message(original_message)
        decrypted = decrypt_message(encrypted)

        assert encrypted != original_message
        assert decrypted == original_message

    def test_encrypt_empty_message(self):
        """Тест шифрования пустого сообщения"""
        original_message = ""
        encrypted = encrypt_message(original_message)
        decrypted = decrypt_message(encrypted)

        assert decrypted == original_message

    def test_encrypt_long_message(self):
        """Тест шифрования длинного сообщения"""
        original_message = "А" * 1000
        encrypted = encrypt_message(original_message)
        decrypted = decrypt_message(encrypted)

        assert decrypted == original_message

    def test_encrypt_unicode_message(self):
        """Тест шифрования Unicode сообщения"""
        original_message = "Тест 测试 テスト 🔒🔐"
        encrypted = encrypt_message(original_message)
        decrypted = decrypt_message(encrypted)

        assert decrypted == original_message

    def test_different_encryptions(self):
        """Тест что одинаковые сообщения шифруются по-разному"""
        message = "Секретное сообщение"
        encrypted1 = encrypt_message(message)
        encrypted2 = encrypt_message(message)

        # Зашифрованные версии должны отличаться из-за разных IV
        assert encrypted1 != encrypted2

        # Но расшифровываться должны в одно и то же
        assert decrypt_message(encrypted1) == message
        assert decrypt_message(encrypted2) == message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

