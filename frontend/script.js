let token = null;
let currentChatId = null;
let ws = null;

// API запросы идут через nginx на /api
const API_BASE_URL = '/api';

function login() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
        alert('Имя пользователя и пароль не могут быть пустыми.');
        return;
    }

    fetch(`${API_BASE_URL}/token`, {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Неверное имя пользователя или пароль.');
        }
        return response.json();
    })
    .then(data => {
        token = data.access_token;
        document.getElementById('auth').style.display = 'none';
        document.getElementById('main').style.display = 'flex';
        loadChats();
        loadOnlineUsers();
    })
    .catch(err => alert('Ошибка входа: ' + err.message));
}

function register() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
        alert('Имя пользователя и пароль не могут быть пустыми.');
        return;
    }

    fetch(`${API_BASE_URL}/register/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка регистрации. Возможно, пользователь уже существует.');
        }
        return response.json();
    })
    .then(data => {
        alert('Пользователь успешно зарегистрирован. Теперь вы можете войти.');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
    })
    .catch(err => alert('Ошибка регистрации: ' + err.message));
}

function loadChats() {
    fetch(`${API_BASE_URL}/chats/`, {
        headers: {'Authorization': `Bearer ${token}`}
    })
    .then(response => response.json())
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
    .then(response => response.json())
    .then(users => {
        const container = document.getElementById('online-users');
        container.innerHTML = `<p>Онлайн: ${users.length} пользователей</p>`;
    });
}

function toggleChatList() {
    const container = document.getElementById('chat-list-container');
    container.classList.toggle('open');
}