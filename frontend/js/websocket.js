// Модуль для работы с WebSocket
const WebSocketManager = {
    connect() {
        if (APP_STATE.ws) {
            APP_STATE.ws.close();
        }

        const wsUrl = `${APP_CONFIG.WS_URL}?token=${APP_STATE.token}`;
        APP_STATE.ws = new WebSocket(wsUrl);

        APP_STATE.ws.onopen = () => {
            console.log('WebSocket соединение установлено');
            APP_STATE.reconnectAttempts = 0;
            UI.showNotification('Подключено к серверу', 'success');
        };

        APP_STATE.ws.onmessage = (event) => {
            this.handleMessage(event.data);
        };

        APP_STATE.ws.onerror = (error) => {
            console.error('WebSocket ошибка:', error);
            UI.showNotification('Ошибка подключения', 'error');
        };

        APP_STATE.ws.onclose = () => {
            console.log('WebSocket соединение закрыто');
            this.handleReconnect();
        };
    },

    handleMessage(data) {
        try {
            const message = JSON.parse(data);

            if (message.type === 'chat_message') {
                if (message.chat_id === APP_STATE.currentChatId) {
                    UI.addMessage(message);
                }
            } else if (message.type === 'system') {
                UI.showNotification(message.content, 'info');
            }
        } catch (error) {
            console.error('Ошибка обработки сообщения:', error);
        }
    },

    handleReconnect() {
        if (APP_STATE.reconnectAttempts < APP_STATE.maxReconnectAttempts) {
            APP_STATE.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, APP_STATE.reconnectAttempts), 10000);

            UI.showNotification(`Переподключение через ${delay / 1000}с...`, 'info');

            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            UI.showNotification('Не удалось подключиться к серверу', 'error');
        }
    },

    sendMessage(message) {
        if (APP_STATE.ws && APP_STATE.ws.readyState === WebSocket.OPEN) {
            APP_STATE.ws.send(JSON.stringify(message));
        } else {
            UI.showNotification('Нет подключения к серверу', 'error');
        }
    },

    disconnect() {
        if (APP_STATE.ws) {
            APP_STATE.ws.close();
            APP_STATE.ws = null;
        }
    },
};

window.WebSocketManager = WebSocketManager;

