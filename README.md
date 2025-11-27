# 🚀 Инструкция по запуску мессенджера

## Быстрый старт

### Способ 1: Docker Compose (рекомендуется)

```bash
# 1. Клонируйте репозиторий (если еще не сделали)
cd C:\Users\prime\PycharmProjects\MIREA_Py_Courcer_paper

# 2. Настройте переменные окружения
# Скопируйте .env.example в .env (файл .env уже создан)
# Или создайте его вручную:
copy .env.example .env

# 3. Отредактируйте .env файл (ВАЖНО для продакшена!)
# Откройте .env в текстовом редакторе и измените:
# - SECRET_KEY на надежный ключ (например: openssl rand -hex 32)
# - POSTGRES_PASSWORD на надежный пароль
# - DATABASE_URL с новым паролем

# 4. Запустите все сервисы
docker-compose up --build

# 5. Откройте браузер
# Фронтенд: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Prometheus: http://localhost:9090
```

### Способ 2: Локальная разработка

#### Backend
```bash
cd backend

# Создайте .env файл в папке backend
# Скопируйте переменные из корневого .env

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
Просто откройте `frontend/index.html` в браузере или используйте любой локальный сервер:
```bash
cd frontend
python -m http.server 3000
```

## ⚙️ Настройка переменных окружения

### Структура .env файла:

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=messenger
DATABASE_URL=postgresql://postgres:your_password@db:5432/messenger

# Redis Configuration
REDIS_URL=redis://redis:6379

# Backend Configuration
SECRET_KEY=your-secret-key-CHANGE-THIS
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ports
NGINX_PORT=80
PROMETHEUS_PORT=9090
```

### Генерация SECRET_KEY

#### Windows PowerShell:
```powershell
# Используйте Python
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Linux/Mac:
```bash
openssl rand -hex 32
```

## 🎨 Что вы увидите

### 1. Страница входа
- Красивый градиентный фон
- Форма входа/регистрации
- Анимации при загрузке

### 2. Главный интерфейс
- Список чатов слева
- Область сообщений справа
- Поле ввода внизу
- Кнопка управления участниками

### 3. На мобильных устройствах
- Адаптивная верстка
- Выдвижное меню
- Полноэкранные чаты

## 🔧 Кастомизация

### Изменение портов

Отредактируйте `.env`:
```env
NGINX_PORT=8080  # Вместо 80
PROMETHEUS_PORT=9091  # Вместо 9090
```

### Изменение цветовой схемы
Отредактируйте `frontend/styles.css`:
```css
:root {
    --primary-color: #667eea;     /* Ваш цвет */
    --secondary-color: #764ba2;   /* Ваш цвет */
}
```

### Изменение API URL (для продакшена)
Отредактируйте `frontend/js/config.js`:
```javascript
const CONFIG = {
    API_URL: 'https://your-api-url.com',
    WS_URL: 'wss://your-api-url.com/ws',
};
```

## 📝 Использование

### Регистрация
1. Введите имя пользователя и пароль
2. Нажмите "Зарегистрироваться"
3. После успеха войдите с теми же данными

### Создание чата
1. Нажмите "Создать чат"
2. Введите название
3. Чат появится в списке

### Отправка сообщений
1. Выберите чат из списка
2. Введите сообщение
3. Нажмите Enter или кнопку "Отправить"

### Управление участниками
1. Откройте чат
2. Нажмите "👥 Участники"
3. Добавляйте или удаляйте пользователей

## 🐛 Решение проблем

### Порт уже занят
```bash
# Измените порты в .env файле
NGINX_PORT=8080
```

### WebSocket не подключается
- Проверьте, запущен ли backend: `docker-compose ps`
- Проверьте логи: `docker-compose logs backend`
- Убедитесь, что порт 8000 доступен

### Не загружаются стили
- Проверьте пути к файлам
- Убедитесь, что папка `js/` существует
- Очистите кэш браузера (Ctrl+Shift+R)

### Ошибка подключения к базе данных
- Проверьте переменные в .env
- Проверьте, запущен ли контейнер db: `docker-compose ps db`
- Проверьте логи: `docker-compose logs db`

### Ошибки в консоли
- Откройте DevTools (F12)
- Проверьте вкладку Console
- Проверьте вкладку Network

## 📱 Тестирование на мобильных

### Chrome DevTools
1. F12 → Toggle Device Toolbar (Ctrl+Shift+M)
2. Выберите устройство (iPhone, iPad, etc.)
3. Проверьте адаптивность

### Реальное устройство
1. Найдите IP вашего компьютера: `ipconfig` (Windows) или `ifconfig` (Linux/Mac)
2. Откройте http://YOUR_IP на мобильном
3. Убедитесь, что устройства в одной сети

## 🔒 Безопасность для продакшена

### Обязательно измените:
- ✅ SECRET_KEY (генерируйте случайную строку)
- ✅ POSTGRES_PASSWORD (используйте надежный пароль)
- ✅ Обновите DATABASE_URL с новым паролем

### Рекомендации:
- Используйте HTTPS/WSS вместо HTTP/WS
- Настройте firewall для ограничения доступа
- Регулярно обновляйте зависимости
- Настройте резервное копирование БД

## 🎯 Следующие шаги

- [ ] Добавить поддержку файлов
- [ ] Реализовать голосовые сообщения
- [ ] Добавить темную тему
- [ ] Создать PWA версию
- [ ] Добавить push-уведомления

## 📞 Полезные команды Docker

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Пересборка
docker-compose up --build

# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs backend

# Перезапуск сервиса
docker-compose restart nginx

# Просмотр запущенных контейнеров
docker-compose ps
```

---

**Приятного использования! 🎉**

