// Главный файл приложения

// Функции аутентификации
async function register() {
    const username = UI.elements.username.value.trim();
    const password = UI.elements.password.value;

    if (!username || !password) {
        UI.showNotification('Заполните все поля', 'error');
        return;
    }

    try {
        await API.register(username, password);
        UI.showNotification('Регистрация успешна! Войдите в систему', 'success');
        UI.clearInputs();
    } catch (error) {
        UI.showNotification(error.message, 'error');
    }
}

async function login() {
    const username = UI.elements.username.value.trim();
    const password = UI.elements.password.value;

    if (!username || !password) {
        UI.showNotification('Заполните все поля', 'error');
        return;
    }

    try {
        const data = await API.login(username, password);

        APP_STATE.token = data.access_token;
        APP_STATE.username = username;

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('username', username);

        UI.clearInputs();
        UI.showMain();

        await loadChats();
        WebSocketManager.connect();

        UI.showNotification(`Добро пожаловать, ${username}!`, 'success');
    } catch (error) {
        UI.showNotification(error.message, 'error');
    }
}

function logout() {
    APP_STATE.token = null;
    APP_STATE.username = null;
    APP_STATE.currentChatId = null;
    APP_STATE.currentChatName = null;

    localStorage.removeItem('token');
    localStorage.removeItem('username');

    WebSocketManager.disconnect();

    UI.showAuth();
    UI.clearMessages();
    UI.updateChatHeader('Выберите чат');
    UI.clearInputs();

    UI.showNotification('Вы вышли из системы', 'info');
}

// Функции для работы с чатами
async function loadChats() {
    try {
        const chats = await API.getChats();
        UI.renderChats(chats);
    } catch (error) {
        UI.showNotification(`Ошибка загрузки чатов: ${error.message}`, 'error');
    }
}

async function createChat() {
    const chatName = prompt('Введите название чата:');

    if (!chatName || !chatName.trim()) {
        UI.showNotification('Название чата не может быть пустым', 'error');
        return;
    }

    try {
        await API.createChat(chatName.trim());
        UI.showNotification('Чат создан успешно', 'success');
        await loadChats();
    } catch (error) {
        UI.showNotification(error.message, 'error');
    }
}

async function selectChat(chatId, chatName) {
    APP_STATE.currentChatId = chatId;
    APP_STATE.currentChatName = chatName;

    UI.updateChatHeader(chatName);
    UI.closeChatList();

    // Обновляем активный чат в списке
    document.querySelectorAll('#chats li').forEach(li => {
        li.classList.remove('active');
        if (parseInt(li.dataset.chatId) === chatId) {
            li.classList.add('active');
        }
    });

    try {
        const messages = await API.getMessages(chatId);
        UI.renderMessages(messages);
    } catch (error) {
        UI.showNotification(`Ошибка загрузки сообщений: ${error.message}`, 'error');
    }
}

// Функции для работы с сообщениями
function sendMessage() {
    const content = UI.elements.messageInput.value.trim();

    if (!content) {
        return;
    }

    if (!APP_STATE.currentChatId) {
        UI.showNotification('Выберите чат', 'error');
        return;
    }

    const message = {
        type: 'chat_message',
        chat_id: APP_STATE.currentChatId,
        content: content,
    };

    WebSocketManager.sendMessage(message);
    UI.elements.messageInput.value = '';
}

// Функции для работы с участниками
async function openMembersModal() {
    if (!APP_STATE.currentChatId) {
        UI.showNotification('Выберите чат', 'error');
        return;
    }

    UI.openMembersModal();
    await UI.renderMembers(APP_STATE.currentChatId);
}

function closeMembersModal() {
    UI.closeMembersModal();
}

async function addMemberToChat(chatId, username) {
    try {
        await API.addMember(chatId, username);
        UI.showNotification(`Пользователь ${username} добавлен`, 'success');
        await UI.renderMembers(chatId);
    } catch (error) {
        UI.showNotification(error.message, 'error');
    }
}

async function removeMemberFromChat(chatId, username) {
    try {
        await API.removeMember(chatId, username);
        UI.showNotification(`Пользователь ${username} удален`, 'success');
        await UI.renderMembers(chatId);
    } catch (error) {
        UI.showNotification(error.message, 'error');
    }
}

function toggleChatList() {
    UI.toggleChatList();
}

// Экспорт функций в глобальную область видимости
window.register = register;
window.login = login;
window.logout = logout;
window.loadChats = loadChats;
window.createChat = createChat;
window.selectChat = selectChat;
window.sendMessage = sendMessage;
window.openMembersModal = openMembersModal;
window.closeMembersModal = closeMembersModal;
window.addMemberToChat = addMemberToChat;
window.removeMemberFromChat = removeMemberFromChat;
window.toggleChatList = toggleChatList;

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    if (event.target === UI.elements.membersModal) {
        closeMembersModal();
    }

    // Закрытие списка чатов на мобильных при клике вне его
    if (window.innerWidth <= 768 &&
        !UI.elements.chatListContainer.contains(event.target) &&
        !event.target.closest('#mobile-menu-toggle')) {
        UI.closeChatList();
    }
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    UI.init();

    // Проверяем, есть ли сохраненная сессия
    if (APP_STATE.token && APP_STATE.username) {
        UI.showMain();
        loadChats();
        WebSocketManager.connect();
    } else {
        UI.showAuth();
    }
});

// Обработка закрытия страницы
window.addEventListener('beforeunload', () => {
    WebSocketManager.disconnect();
});


