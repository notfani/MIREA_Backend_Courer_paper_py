// Модуль для работы с API
const API = {
    // Базовый метод для запросов
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (APP_STATE.token) {
            defaultOptions.headers['Authorization'] = `Bearer ${APP_STATE.token}`;
        }

        const response = await fetch(`${APP_CONFIG.API_URL}${url}`, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
            throw new Error(error.detail || 'Произошла ошибка');
        }

        return response.json();
    },

    // Регистрация
    async register(username, password) {
        return this.request('/register', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
    },

    // Вход
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        return this.request('/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });
    },

    // Получение списка чатов
    async getChats() {
        return this.request('/chats');
    },

    // Создание чата
    async createChat(chatName) {
        return this.request('/chats', {
            method: 'POST',
            body: JSON.stringify({ name: chatName }),
        });
    },

    // Получение сообщений чата
    async getMessages(chatId) {
        return this.request(`/chats/${chatId}/messages`);
    },

    // Получение участников чата
    async getChatMembers(chatId) {
        return this.request(`/chats/${chatId}/members`);
    },

    // Получение всех пользователей
    async getAllUsers() {
        return this.request('/users');
    },

    // Добавление участника в чат
    async addMember(chatId, username) {
        return this.request(`/chats/${chatId}/members`, {
            method: 'POST',
            body: JSON.stringify({ username }),
        });
    },

    // Удаление участника из чата
    async removeMember(chatId, username) {
        return this.request(`/chats/${chatId}/members/${username}`, {
            method: 'DELETE',
        });
    },
};

window.API = API;

