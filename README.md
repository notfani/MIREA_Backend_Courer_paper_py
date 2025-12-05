# Messenger Application

Веб-приложение для обмена сообщениями в реальном времени с поддержкой WebSocket, построенное на FastAPI и PostgreSQL.

## Описание

Приложение представляет собой полнофункциональный мессенджер с возможностью создания чатов, обмена сообщениями в реальном времени и управления участниками. Включает мониторинг через Prometheus и кэширование через Redis.

## Технологический стек

**Backend:**
- FastAPI
- PostgreSQL
- Redis
- WebSocket
- SQLAlchemy

**Frontend:**
- Vanilla JavaScript
- HTML5/CSS3
- WebSocket API

**Инфраструктура:**
- Docker & Docker Compose
- Nginx
- Prometheus

## Требования

- Docker 20.10+
- Docker Compose 1.29+

Либо для локальной разработки:
- Python 3.9+
- PostgreSQL 13+
- Redis 6+

## Установка и запуск

### Использование Docker Compose

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd MIREA_Py_Courcer_paper
```

2. Создайте файл `.env` на основе примера:
```bash
copy .env.example .env
```

3. Настройте переменные окружения в `.env`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your_secure_password>
POSTGRES_DB=messenger
DATABASE_URL=postgresql://postgres:<your_password>@db:5432/messenger

REDIS_URL=redis://redis:6379

SECRET_KEY=<generate_secure_key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

NGINX_PORT=80
PROMETHEUS_PORT=9090
```

4. Запустите приложение:
```bash
docker-compose up --build
```

5. Доступ к сервисам:
- Приложение: http://localhost
- API: http://localhost:8000
- API документация: http://localhost:8000/docs
- Prometheus: http://localhost:9090

### Локальная разработка

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
python -m http.server 3000
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|---------------------|
| `POSTGRES_USER` | Имя пользователя PostgreSQL | postgres |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | - |
| `POSTGRES_DB` | Название базы данных | messenger |
| `DATABASE_URL` | URL подключения к БД | - |
| `REDIS_URL` | URL подключения к Redis | redis://redis:6379 |
| `SECRET_KEY` | Секретный ключ для JWT | - |
| `ALGORITHM` | Алгоритм шифрования | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена | 30 |

### Генерация SECRET_KEY

Windows PowerShell:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Linux/macOS:
```bash
openssl rand -hex 32
```

### Настройка портов

Отредактируйте `.env` для изменения портов:
```env
NGINX_PORT=8080
PROMETHEUS_PORT=9091
```

### Настройка API URL для продакшена

Отредактируйте `frontend/js/config.js`:
```javascript
const CONFIG = {
    API_URL: 'https://your-domain.com',
    WS_URL: 'wss://your-domain.com/ws',
};
```

## API документация

После запуска приложения автоматически сгенерированная документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Управление Docker контейнерами

Запуск в фоновом режиме:
```bash
docker-compose up -d
```

Остановка:
```bash
docker-compose down
```

Просмотр логов:
```bash
docker-compose logs
docker-compose logs backend
```

Перезапуск сервиса:
```bash
docker-compose restart nginx
```

Пересборка:
```bash
docker-compose up --build
```

## Безопасность

### Рекомендации для продакшена

1. Используйте надежные пароли для `POSTGRES_PASSWORD` и `SECRET_KEY`
2. Настройте HTTPS/WSS вместо HTTP/WS
3. Ограничьте доступ к портам через firewall
4. Регулярно обновляйте зависимости
5. Настройте резервное копирование базы данных
6. Используйте переменные окружения для конфиденциальных данных

## Диагностика проблем

### Порт занят
Измените порты в `.env` файле.

### Ошибка подключения к базе данных
Проверьте переменные в `.env` и убедитесь, что контейнер БД запущен:
```bash
docker-compose ps db
docker-compose logs db
```

### WebSocket не подключается
Проверьте статус backend:
```bash
docker-compose ps backend
docker-compose logs backend
```

### Отладка фронтенда
Откройте консоль разработчика (F12) и проверьте вкладки Console и Network.

## Архитектура

```
┌─────────────┐
│   Nginx     │ (Reverse Proxy)
└──────┬──────┘
       │
┌──────▼──────┐
│  Frontend   │ (HTML/CSS/JS)
└──────┬──────┘
       │
┌──────▼──────┐
│  Backend    │ (FastAPI + WebSocket)
└──┬────┬─────┘
   │    │
   │    └──────┐
   │           │
┌──▼─────┐ ┌──▼─────┐
│Postgres│ │ Redis  │
└────────┘ └────────┘
```

## Лицензия

[MIT Licence](LICENSE)

## Контакты

[email](mailto:yin-nylon-lisp@duck.com)
