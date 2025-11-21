let token = null;
let currentChatId = null;
let ws = null;

// API запросы идут через nginx на /api
const API_BASE_URL = '/api';

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
        console.log('Token saved, switching to main interface');

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
        alert('Пользователь успешно зарегистрирован! Теперь войдите в систему.');
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
        document.getElementById('auth').style.display = 'block';
        document.getElementById('main').style.display = 'none';
        token = null;
    });
}

function openChat(chatId, chatName) {
    currentChatId = chatId;
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
    if (!currentChatId) return;
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
    if (ws) ws.close();
    // WebSocket через nginx на /ws
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${chatId}`;

    ws = new WebSocket(wsUrl);

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        addMessageToDOM(data);
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
    .then(response => {
        if (!response.ok) {
            throw new Error('Не удалось загрузить пользователей');
        }
        return response.json();
    })
    .then(users => {
        const container = document.getElementById('online-users');
        container.innerHTML = `<p>Онлайн: ${users.length} пользователей</p>`;
    })
    .catch(err => {
        console.error('Ошибка загрузки онлайн пользователей:', err);
    });
}

function toggleChatList() {
    const container = document.getElementById('chat-list-container');
    container.classList.toggle('open');
}