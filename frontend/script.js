let token = localStorage.getItem('auth_token') || null;
let currentChatId = null;
let currentChat = null;  // Сохраняем информацию о текущем чате
let ws = null;

// API запросы идут через nginx на /api
const API_BASE_URL = '/api';

// Проверка токена при загрузке страницы
window.addEventListener('DOMContentLoaded', function() {
    if (token) {
        // Проверяем валидность токена
        checkTokenAndLogin();
    }
});

function checkTokenAndLogin() {
    fetch(`${API_BASE_URL}/chats/`, {
        headers: {'Authorization': `Bearer ${token}`}
    })
    .then(response => {
        if (response.ok) {
            // Токен валиден, входим
            document.getElementById('auth').style.display = 'none';
            document.getElementById('main').style.display = 'flex';
            loadChats();
        } else {
            // Токен невалиден, удаляем
            localStorage.removeItem('auth_token');
            token = null;
        }
    })
    .catch(() => {
        localStorage.removeItem('auth_token');
        token = null;
    });
}

function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        alert('Введите логин и пароль');
        return;
    }

    if (username.length < 3 || username.length > 50) {
        alert('Логин должен быть от 3 до 50 символов');
        return;
    }

    if (password.length < 6) {
        alert('Пароль должен быть минимум 6 символов');
        return;
    }

    if (password.length > 72) {
        alert('Пароль слишком длинный (максимум 72 символа)');
        return;
    }

    console.log('Starting login attempt for:', username);

    fetch(`${API_BASE_URL}/token`, {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
    })
    .then(async response => {
        console.log('Token response status:', response.status);
        if (!response.ok) {
            let msg = 'Неверные учетные данные';
            try {
                const data = await response.json();
                msg = data.detail || msg;
            } catch {}
            console.error('Login failed:', msg);
            throw new Error(msg);
        }
        return response.json();
    })
    .then(data => {
        console.log('Token response data:', data);
        if (!data || !data.access_token) {
            console.error('No access token in response');
            throw new Error('Не получен токен авторизации');
        }

        // Сохраняем токен
        token = data.access_token;
        localStorage.setItem('auth_token', token);
        console.log('Token saved to localStorage, switching to main interface');

        // Переключаем интерфейс
        document.getElementById('auth').style.display = 'none';
        document.getElementById('main').style.display = 'flex';

        // Загружаем данные
        loadChats();
        loadOnlineUsers();
        console.log('Successful login complete');
    })
    .catch(err => {
        console.error('Login error caught:', err);
        alert(err.message);

        // Гарантируем сброс состояния при ошибке
        token = null;
        localStorage.removeItem('auth_token');
        document.getElementById('auth').style.display = 'block';
        document.getElementById('main').style.display = 'none';
        console.log('Login failed, staying on auth screen');
    });
}

function register() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        alert('Введите логин и пароль');
        return;
    }

    if (username.length < 3 || username.length > 50) {
        alert('Логин должен быть от 3 до 50 символов');
        return;
    }

    if (password.length < 6) {
        alert('Пароль должен быть минимум 6 символов');
        return;
    }

    if (password.length > 72) {
        alert('Пароль слишком длинный (максимум 72 символа)');
        return;
    }

    console.log('Starting registration for:', username);

    fetch(`${API_BASE_URL}/register/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    })
    .then(async response => {
        console.log('Registration response status:', response.status);
        if (!response.ok) {
            let msg = 'Ошибка регистрации';
            try {
                const data = await response.json();
                msg = data.detail || msg;
            } catch {}
            console.error('Registration failed:', msg);
            throw new Error(msg);
        }
        return response.json();
    })
    .then(data => {
        console.log('Registration successful:', data);
        alert('Пользователь успешно зарегистрирован! Выполняется вход...');

        // Автоматически входим после регистрации
        login();
    })
    .catch(err => {
        console.error('Registration error:', err);
        alert(err.message);
    });
}

function loadChats() {
    if (!token) {
        console.error('No token available - cannot load chats');
        document.getElementById('auth').style.display = 'block';
        document.getElementById('main').style.display = 'none';
        return;
    }

    fetch(`${API_BASE_URL}/chats/`, {
        headers: {'Authorization': `Bearer ${token}`}
    })
    .then(response => {
        if (!response.ok) {
            console.error('Failed to load chats, status:', response.status);
            throw new Error('Не удалось загрузить чаты');
        }
        return response.json();
    })
    .then(chats => {
        const ul = document.getElementById('chats');
        ul.innerHTML = '';
        chats.forEach(chat => {
            const li = document.createElement('li');
            li.textContent = chat.name;
            li.onclick = () => {
                openChat(chat.id, chat.name);
                if (window.innerWidth < 768) {
                    toggleChatList(); // Скрыть список чатов на мобильных
                }
            };
            ul.appendChild(li);
        });
    })
    .catch(err => {
        console.error('Ошибка загрузки чатов:', err);
        // Если токен невалиден, возвращаемся к экрану авторизации
        alert('Сессия истекла. Войдите снова.');
        logout();
    });
}

function logout() {
    token = null;
    localStorage.removeItem('auth_token');
    document.getElementById('auth').style.display = 'block';
    document.getElementById('main').style.display = 'none';
    if (ws) {
        ws.close();
        ws = null;
    }
    currentChatId = null;
}

function openChat(chatId, chatName) {
    console.log(`Opening chat: id=${chatId}, name=${chatName}`);
    currentChatId = chatId;

    // Загружаем информацию о чате
    fetch(`${API_BASE_URL}/chats/${chatId}`, {
        headers: {'Authorization': `Bearer ${token}`}
    })
    .then(response => response.json())
    .then(chat => {
        currentChat = chat;
        // Показываем кнопку управления участниками только для групповых чатов
        const manageMembersBtn = document.getElementById('manage-members-btn');
        if (chat.is_group) {
            manageMembersBtn.style.display = 'inline-block';
        } else {
            manageMembersBtn.style.display = 'none';
        }
    })
    .catch(err => {
        console.error('Ошибка загрузки информации о чате:', err);
    });

    document.getElementById('chat-name').textContent = chatName;
    loadMessages(chatId);
    connectWebSocket(chatId);
}

function loadMessages(chatId) {
    fetch(`${API_BASE_URL}/messages/${chatId}`, {
        headers: {'Authorization': `Bearer ${token}`}
    })
    .then(response => response.json())
    .then(messages => {
        const container = document.getElementById('messages');
        container.innerHTML = '';
        messages.forEach(msg => {
            addMessageToDOM(msg);
        });
        container.scrollTop = container.scrollHeight;
    });
}

function addMessageToDOM(msg) {
    const container = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message';
    div.textContent = `${msg.user.username}: ${msg.content}`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function sendMessage() {
    console.log(`Attempting to send message. currentChatId: ${currentChatId}`);
    if (!currentChatId) {
        alert("Пожалуйста, сначала выберите чат из списка слева.");
        return;
    }
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    if (!content) return;

    fetch(`${API_BASE_URL}/messages/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({content, chat_id: currentChatId})
    })
    .then(() => {
        input.value = '';
    });
}

function connectWebSocket(chatId) {
    console.log("Attempting to connect WebSocket. Token:", token);
    if (!token) {
        alert("Ошибка: токен авторизации отсутствует. Попробуйте войти снова.");
        return;
    }
    if (ws) ws.close();
    // WebSocket через nginx на /ws
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${chatId}?token=${token}`;
    console.log("Connecting to WebSocket URL:", wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = function(event) {
        console.log("WebSocket connection opened:", event);
    };

    ws.onmessage = function(event) {
        console.log("WebSocket message received:", event.data);
        try {
            const data = JSON.parse(event.data);
            addMessageToDOM(data);
        } catch (e) {
            console.error("Error parsing WebSocket message or adding to DOM:", e, event.data);
        }
    };

    ws.onclose = function(event) {
        console.log("WebSocket connection closed:", event);
    };
    
    ws.onerror = function(event) {
        console.error("WebSocket error:", event);
    };
}

function createChat() {
    const name = prompt('Название чата:');
    if (!name) return;

    fetch(`${API_BASE_URL}/chats/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({name, is_group: true, members: []})
    })
    .then(() => loadChats());
}

function loadOnlineUsers() {
    fetch(`${API_BASE_URL}/online-users/`)
    const container = document.getElementById('chat-list-container');
    container.classList.toggle('open');
}

// Функции для управления участниками чата
function openMembersModal() {
    if (!currentChat) {
        alert('Пожалуйста, сначала выберите чат');
        return;
    }

    const modal = document.getElementById('members-modal');
    modal.style.display = 'block';

    // Отображаем текущих участников
    displayCurrentMembers();

    // Загружаем список доступных пользователей
    loadAvailableUsers();
}

function closeMembersModal() {
    const modal = document.getElementById('members-modal');
    modal.style.display = 'none';
}

function displayCurrentMembers() {
    const membersList = document.getElementById('members-list');
    membersList.innerHTML = '';

    if (!currentChat || !currentChat.members) {
        membersList.innerHTML = '<p>Нет участников</p>';
        return;
    }

    currentChat.members.forEach(member => {
        const div = document.createElement('div');
        div.className = 'user-item';
        div.innerHTML = `
            <span>${member.username}</span>
            <span class="member-badge">Участник</span>
        `;
        membersList.appendChild(div);
    });
}

function loadAvailableUsers() {
    fetch(`${API_BASE_URL}/users/`, {
        headers: {'Authorization': `Bearer ${token}`}
    })
    .then(response => response.json())
    .then(users => {
        const availableUsersList = document.getElementById('available-users-list');
        availableUsersList.innerHTML = '';

        // Получаем ID текущих участников
        const currentMemberIds = currentChat.members.map(m => m.id);

        // Фильтруем пользователей, которые еще не в чате
        const availableUsers = users.filter(user => !currentMemberIds.includes(user.id));

        if (availableUsers.length === 0) {
            availableUsersList.innerHTML = '<p>Все пользователи уже в чате</p>';
            return;
        }

        availableUsers.forEach(user => {
            const div = document.createElement('div');
            div.className = 'user-item';
            div.innerHTML = `
                <span>${user.username}</span>
                <button onclick="addUserToChat(${user.id}, '${user.username}')">Добавить</button>
            `;
            availableUsersList.appendChild(div);
        });
    })
    .catch(err => {
        console.error('Ошибка загрузки пользователей:', err);
        alert('Не удалось загрузить список пользователей');
    });
}

function addUserToChat(userId, username) {
    if (!currentChatId) {
        alert('Чат не выбран');
        return;
    }

    fetch(`${API_BASE_URL}/chats/${currentChatId}/add-user/${userId}`, {
        method: 'POST',
        headers: {'Authorization': `Bearer ${token}`}
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Ошибка добавления пользователя');
            });
        }
        return response.json();
    })
    .then(data => {
        alert(`Пользователь ${username} добавлен в чат!`);

        // Обновляем информацию о текущем чате
        return fetch(`${API_BASE_URL}/chats/${currentChatId}`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
    })
    .then(response => response.json())
    .then(chat => {
        currentChat = chat;
        // Обновляем отображение
        displayCurrentMembers();
        loadAvailableUsers();
    })
    .catch(err => {
        console.error('Ошибка добавления пользователя:', err);
        alert(err.message);
    });
}

// Закрыть модальное окно при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('members-modal');
    if (event.target === modal) {
        closeMembersModal();
    }
}
