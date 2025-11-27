// Конфигурация приложения
const CONFIG = {
    API_URL: window.location.origin,
    WS_URL: `ws://${window.location.host}/ws`,
};

// Состояние приложения
const state = {
    token: localStorage.getItem('token') || null,
    username: localStorage.getItem('username') || null,
    currentChatId: null,
    currentChatName: null,
    ws: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
};

// Экспорт для использования в других модулях
window.APP_CONFIG = CONFIG;
window.APP_STATE = state;

