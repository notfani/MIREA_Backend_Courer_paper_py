// Модуль для работы с UI
const UI = {
    elements: {},

    init() {
        // Кэшируем элементы DOM
        this.elements = {
            auth: document.getElementById('auth'),
            main: document.getElementById('main'),
            username: document.getElementById('username'),
            password: document.getElementById('password'),
            chatsList: document.getElementById('chats'),
            messages: document.getElementById('messages'),
            messageInput: document.getElementById('message-input'),
            chatName: document.getElementById('chat-name'),
            manageMembersBtn: document.getElementById('manage-members-btn'),
            membersModal: document.getElementById('members-modal'),
            membersList: document.getElementById('members-list'),
            availableUsersList: document.getElementById('available-users-list'),
            chatListContainer: document.getElementById('chat-list-container'),
        };

        // Добавляем обработчик Enter для отправки сообщений
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Обработчик Enter для входа
        this.elements.password.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                login();
            }
        });

        // Создаем контейнер для уведомлений
        this.createNotificationContainer();
    },

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
        this.elements.notificationContainer = container;
    },

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            padding: 15px 20px;
            border-radius: 12px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideInRight 0.3s ease-out;
            max-width: 300px;
            word-wrap: break-word;
        `;

        const colors = {
            success: '#48bb78',
            error: '#f56565',
            info: '#667eea',
        };

        notification.style.background = colors[type] || colors.info;

        this.elements.notificationContainer.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    showAuth() {
        this.elements.auth.style.display = 'flex';
        this.elements.main.style.display = 'none';
    },

    showMain() {
        this.elements.auth.style.display = 'none';
        this.elements.main.style.display = 'grid';
    },

    clearInputs() {
        this.elements.username.value = '';
        this.elements.password.value = '';
        this.elements.messageInput.value = '';
    },

    renderChats(chats) {
        this.elements.chatsList.innerHTML = '';

        if (chats.length === 0) {
            const emptyMessage = document.createElement('li');
            emptyMessage.textContent = 'Нет доступных чатов';
            emptyMessage.style.cssText = 'text-align: center; opacity: 0.6; cursor: default;';
            this.elements.chatsList.appendChild(emptyMessage);
            return;
        }

        chats.forEach(chat => {
            const li = document.createElement('li');
            li.textContent = chat.name;
            li.dataset.chatId = chat.id;

            if (chat.id === APP_STATE.currentChatId) {
                li.classList.add('active');
            }

            li.onclick = () => selectChat(chat.id, chat.name);
            this.elements.chatsList.appendChild(li);
        });
    },

    updateChatHeader(chatName) {
        this.elements.chatName.textContent = chatName;
        this.elements.manageMembersBtn.style.display = chatName === 'Выберите чат' ? 'none' : 'inline-block';
    },

    clearMessages() {
        this.elements.messages.innerHTML = '';
    },

    addMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.username === APP_STATE.username ? 'own' : 'other'}`;

        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        headerDiv.textContent = message.username;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message.content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(message.timestamp);

        messageDiv.appendChild(headerDiv);
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);

        this.elements.messages.appendChild(messageDiv);
        this.scrollToBottom();
    },

    renderMessages(messages) {
        this.clearMessages();
        messages.forEach(message => this.addMessage(message));
    },

    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    },

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        const timeStr = date.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        if (diffDays === 0) {
            return timeStr;
        } else if (diffDays === 1) {
            return `Вчера ${timeStr}`;
        } else {
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    },

    openMembersModal() {
        this.elements.membersModal.style.display = 'block';
    },

    closeMembersModal() {
        this.elements.membersModal.style.display = 'none';
    },

    async renderMembers(chatId) {
        try {
            const [members, allUsers] = await Promise.all([
                API.getChatMembers(chatId),
                API.getAllUsers(),
            ]);

            // Отображаем текущих участников
            this.elements.membersList.innerHTML = '';
            members.forEach(member => {
                const userDiv = this.createUserItem(member, 'remove', chatId);
                this.elements.membersList.appendChild(userDiv);
            });

            // Отображаем доступных пользователей (не в чате)
            this.elements.availableUsersList.innerHTML = '';
            const memberUsernames = members.map(m => m.username);
            const availableUsers = allUsers.filter(u => !memberUsernames.includes(u.username));

            if (availableUsers.length === 0) {
                const emptyDiv = document.createElement('div');
                emptyDiv.textContent = 'Все пользователи уже в чате';
                emptyDiv.style.cssText = 'text-align: center; opacity: 0.6; padding: 15px;';
                this.elements.availableUsersList.appendChild(emptyDiv);
            } else {
                availableUsers.forEach(user => {
                    const userDiv = this.createUserItem(user, 'add', chatId);
                    this.elements.availableUsersList.appendChild(userDiv);
                });
            }
        } catch (error) {
            this.showNotification(`Ошибка загрузки участников: ${error.message}`, 'error');
        }
    },

    createUserItem(user, action, chatId) {
        const userDiv = document.createElement('div');
        userDiv.className = 'user-item';

        const username = document.createElement('span');
        username.textContent = user.username;

        const button = document.createElement('button');
        button.className = action === 'add' ? 'add-btn' : 'remove-btn';
        button.textContent = action === 'add' ? '+ Добавить' : '✕ Удалить';

        if (action === 'add') {
            button.onclick = () => addMemberToChat(chatId, user.username);
        } else {
            button.onclick = () => removeMemberFromChat(chatId, user.username);
        }

        userDiv.appendChild(username);
        userDiv.appendChild(button);

        return userDiv;
    },

    toggleChatList() {
        this.elements.chatListContainer.classList.toggle('active');
    },

    closeChatList() {
        this.elements.chatListContainer.classList.remove('active');
    },
};

// Добавляем стили для анимаций уведомлений
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

window.UI = UI;

