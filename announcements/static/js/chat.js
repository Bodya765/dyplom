// WebSocket з'єднання для чату
let chatSocket = null;
// WebSocket з'єднання для списку чатів
let chatListSocket = null;
// Ідентифікатор для відкладеного оновлення прокрутки
let scrollUpdateTimeout = null;
// Флаг, що показує, чи був прокручений чат до кінця
let wasScrolledToBottom = true;

/**
 * Підключаємо WebSocket для чату
 */
function connectToChat(roomId) {
    const chatSocketUrl = `ws://${window.location.host}/ws/chat/${roomId}/`;

    chatSocket = new WebSocket(chatSocketUrl);

    chatSocket.onopen = function(e) {
        console.log('WebSocket з\'єднання відкрито');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);

        // Перевіряємо, чи прокручений чат до кінця
        const messagesContainer = document.getElementById('messagesContainer');
        wasScrolledToBottom = isScrolledToBottom(messagesContainer);

        if (data.type === 'message') {
            // Додаємо повідомлення в чат
            appendMessage(data);

            // Оновлюємо прокрутку, якщо чат був прокручений до кінця
            if (wasScrolledToBottom) {
                clearTimeout(scrollUpdateTimeout);
                scrollUpdateTimeout = setTimeout(() => {
                    scrollToBottom(messagesContainer);
                }, 100);
            }

            // Позначаємо повідомлення як прочитані, якщо вони не від поточного користувача
            if (data.sender_id !== currentUserId) {
                markMessagesAsRead(roomId);
            }
        } else if (data.type === 'typing') {
            // Показуємо/приховуємо індикатор "користувач пише"
            const typingIndicator = document.getElementById('typingIndicator');

            if (data.user_id !== currentUserId) {
                if (data.is_typing) {
                    typingIndicator.style.display = 'flex';
                } else {
                    typingIndicator.style.display = 'none';
                }
            }
        } else if (data.type === 'status') {
            // Оновлюємо статус користувача
            const otherUserStatus = document.getElementById('otherUserStatus');

            if (data.user_id !== currentUserId) {
                if (data.status === 'online') {
                    otherUserStatus.textContent = 'онлайн';
                    otherUserStatus.className = 'status online';
                } else {
                    otherUserStatus.textContent = 'офлайн';
                    otherUserStatus.className = 'status offline';
                }
            }
        } else if (data.type === 'messages_read') {
            // Оновлюємо статус прочитання повідомлень
            if (data.user_id !== currentUserId) {
                const messages = document.querySelectorAll('.message.sent');
                messages.forEach(message => {
                    const readStatus = message.querySelector('.message-read-status');
                    if (readStatus) {
                        readStatus.textContent = 'Прочитано';
                    }
                });
            }
        }
    };

    chatSocket.onclose = function(e) {
        console.error('WebSocket з\'єднання закрито');

        // Спроба повторного з'єднання через 5 секунд
        setTimeout(() => {
            connectToChat(roomId);
        }, 5000);
    };

    chatSocket.onerror = function(e) {
        console.error('WebSocket помилка:', e);
    };
}

/**
 * Підключаємо WebSocket для оновлення списку чатів
 */
function connectToChatList() {
    const chatListSocketUrl = `ws://${window.location.host}/ws/chat_list/`;

    chatListSocket = new WebSocket(chatListSocketUrl);

    chatListSocket.onopen = function(e) {
        console.log('WebSocket з\'єднання для списку чатів відкрито');
    };

    chatListSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);

        if (data.type === 'chat_list_update') {
            // Оновлюємо список чатів
            loadChatList();
        }
    };

    chatListSocket.onclose = function(e) {
        console.error('WebSocket з\'єднання для списку чатів закрито');

        // Спроба повторного з'єднання через 5 секунд
        setTimeout(() => {
            connectToChatList();
        }, 5000);
    };

    chatListSocket.onerror = function(e) {
        console.error('WebSocket помилка:', e);
    };
}

/**
 * Відправляємо повідомлення через WebSocket
 */
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (message && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'message',
            'message': message
        }));

        messageInput.value = '';

        // Скидаємо статус "користувач пише"
        sendTypingStatus(false);
    }
}

/**
 * Відправляємо статус "користувач пише" через WebSocket
 */
function sendTypingStatus(isTyping) {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'typing',
            'is_typing': isTyping
        }));
    }
}

/**
 * Завантажуємо історію повідомлень з API
 */
function loadMessages(roomId) {
    fetch(`/api/messages/${roomId}/`)
        .then(response => response.json())
        .then(messages => {
            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = '';

            if (messages.length === 0) {
                const emptyMessage = document.createElement('div');
                emptyMessage.className = 'messages-empty';
                emptyMessage.textContent = 'Ще немає повідомлень. Почніть розмову!';
                messagesContainer.appendChild(emptyMessage);
            } else {
                messages.forEach(message => {
                    appendMessage(message);
                });
            }

            // Прокручуємо до останнього повідомлення
            scrollToBottom(messagesContainer);

            // Оновлюємо статус користувача
            updateUserStatus();
        })
        .catch(error => {
            console.error('Помилка при завантаженні повідомлень:', error);

            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = '<div class="messages-error">Помилка при завантаженні повідомлень. Спробуйте оновити сторінку.</div>';
        });
}

/**
 * Додаємо повідомлення в чат
 */
function appendMessage(message) {
    const messagesContainer = document.getElementById('messages');

    // Видаляємо повідомлення про відсутність повідомлень, якщо воно є
    const emptyMessage = messagesContainer.querySelector('.messages-empty');
    if (emptyMessage) {
        messagesContainer.removeChild(emptyMessage);
    }

    // Створюємо елемент повідомлення
    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.sender_id == currentUserId ? 'sent' : 'received'}`;
    messageElement.setAttribute('data-message-id', message.id);

    // Додаємо текст повідомлення
    messageElement.textContent = message.content;

    // Додаємо час повідомлення
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';

    // Форматуємо дату для відображення
    const messageDate = new Date(message.timestamp);
    let timeText = '';

    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);

    if (messageDate.toDateString() === now.toDateString()) {
        // Сьогодні: показуємо тільки час
        timeText = messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (messageDate.toDateString() === yesterday.toDateString()) {
        // Вчора: показуємо "Вчора" і час
        timeText = `Вчора, ${messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else {
        // Інші дні: показуємо дату і час
        timeText = `${messageDate.toLocaleDateString()} ${messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    timeElement.textContent = timeText;
    messageElement.appendChild(timeElement);

    // Додаємо статус прочитання для власних повідомлень
    if (message.sender_id == currentUserId) {
        const readStatusElement = document.createElement('div');
        readStatusElement.className = 'message-read-status';
        readStatusElement.textContent = message.is_read ? 'Прочитано' : '';
        messageElement.appendChild(readStatusElement);
    }

    // Додаємо повідомлення в контейнер
    messagesContainer.appendChild(messageElement);
}

/**
 * Завантажуємо список чатів з API
 */
function loadChatList() {
    fetch('/api/chat_rooms/')
        .then(response => response.json())
        .then(rooms => {
            const chatList = document.getElementById('chatList');
            chatList.innerHTML = '';

            if (rooms.length === 0) {
                const emptyMessage = document.createElement('div');
                emptyMessage.className = 'chat-list-empty';
                emptyMessage.textContent = 'У вас ще немає чатів.';
                chatList.appendChild(emptyMessage);
            } else {
                rooms.forEach(room => {
                    appendChatItem(room);
                });
            }

            // Позначаємо активний чат, якщо ми на сторінці чату
            if (typeof roomId !== 'undefined') {
                const activeChat = chatList.querySelector(`.chat-item[data-chat-id="${roomId}"]`);
                if (activeChat) {
                    activeChat.classList.add('active');
                }
            }
        })
        .catch(error => {
            console.error('Помилка при завантаженні списку чатів:', error);

            const chatList = document.getElementById('chatList');
            chatList.innerHTML = '<div class="chat-list-error">Помилка при завантаженні списку чатів. Спробуйте оновити сторінку.</div>';
        });
}

/**
 * Додаємо елемент чату в список
 */
function appendChatItem(room) {
    const chatList = document.getElementById('chatList');

    // Створюємо елемент чату
    const chatItem = document.createElement('div');
    chatItem.className = 'chat-item';
    chatItem.setAttribute('data-chat-id', room.id);
    chatItem.setAttribute('data-user-id', room.other_user_id);
    chatItem.setAttribute('data-username', room.other_username);

    // Додаємо обробник кліку
    chatItem.addEventListener('click', function() {
        window.location.href = `/room/${room.id}/`;
    });

    // Ліва частина (інформація про чат)
    const chatItemLeft = document.createElement('div');
    chatItemLeft.className = 'chat-item-left';

    // Заголовок чату
    const chatItemHeader = document.createElement('div');
    chatItemHeader.className = 'chat-item-header';

    // Ім'я співрозмовника
    const chatName = document.createElement('div');
    chatName.className = 'chat-name';
    chatName.textContent = room.other_username;

    // Час останнього повідомлення
    const chatTime = document.createElement('div');
    chatTime.className = 'chat-time';

    if (room.last_message_time) {
        const messageDate = new Date(room.last_message_time);
        let timeText = '';

        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);

        if (messageDate.toDateString() === now.toDateString()) {
            // Сьогодні: показуємо тільки час
            timeText = messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (messageDate.toDateString() === yesterday.toDateString()) {
            // Вчора: показуємо "Вчора"
            timeText = 'Вчора';
        } else {
            // Інші дні: показуємо дату
            timeText = messageDate.toLocaleDateString();
        }

        chatTime.textContent = timeText;
    }

    chatItemHeader.appendChild(chatName);
    chatItemHeader.appendChild(chatTime);

    // Останнє повідомлення
    const chatLastMessage = document.createElement('div');
    chatLastMessage.className = 'chat-last-message';

    if (room.is_typing) {
        chatLastMessage.textContent = 'набирає повідомлення...';
        chatLastMessage.style.fontStyle = 'italic';
        chatLastMessage.style.color = '#4568dc';
    } else {
        chatLastMessage.textContent = room.last_message || 'Немає повідомлень';
    }

    chatItemLeft.appendChild(chatItemHeader);
    chatItemLeft.appendChild(chatLastMessage);

    // Права частина (індикатори)
    const chatItemRight = document.createElement('div');
    chatItemRight.className = 'chat-item-right';

    // Статус онлайн/офлайн
    const statusIndicator = document.createElement('div');
    statusIndicator.className = `status ${room.is_online ? 'online' : 'offline'}`;
    statusIndicator.textContent = room.is_online ? 'онлайн' : 'офлайн';

    // Кількість непрочитаних повідомлень
    if (room.unread_count > 0) {
        const unreadBadge = document.createElement('div');
        unreadBadge.className = 'unread-badge';
        unreadBadge.textContent = room.unread_count > 99 ? '99+' : room.unread_count;
        chatItemRight.appendChild(unreadBadge);
    }

    chatItemRight.appendChild(statusIndicator);

    // Додаємо всі частини в елемент чату
    chatItem.appendChild(chatItemLeft);
    chatItem.appendChild(chatItemRight);

    // Додаємо елемент чату в список
    chatList.appendChild(chatItem);
}

/**
 * Фільтруємо список чатів за іменем користувача
 */
function filterChatList(query) {
    const chatItems = document.querySelectorAll('.chat-item');
    query = query.toLowerCase();

    chatItems.forEach(item => {
        const username = item.getAttribute('data-username').toLowerCase();

        if (username.includes(query)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * Позначаємо повідомлення як прочитані через API
 */
function markMessagesAsRead(roomId) {
    fetch(`/api/mark_read/${roomId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            // Відправляємо повідомлення про прочитання через WebSocket
            chatSocket.send(JSON.stringify({
                'type': 'read_messages'
            }));
        }
    })
    .catch(error => {
        console.error('Помилка при позначенні повідомлень як прочитаних:', error);
    });
}

/**
 * Оновлюємо статус користувача (онлайн/офлайн)
 */
function updateUserStatus() {
    const otherUserStatus = document.getElementById('otherUserStatus');

    if (otherUserStatus) {
        fetch(`/api/chat_rooms/`)
            .then(response => response.json())
            .then(rooms => {
                if (typeof otherUserId !== 'undefined') {
                    const room = rooms.find(r => r.other_user_id === otherUserId);

                    if (room) {
                        if (room.is_online) {
                            otherUserStatus.textContent = 'онлайн';
                            otherUserStatus.className = 'status online';
                        } else {
                            otherUserStatus.textContent = 'офлайн';
                            otherUserStatus.className = 'status offline';
                        }

                        // Перевіряємо, чи користувач набирає повідомлення
                        const typingIndicator = document.getElementById('typingIndicator');

                        if (room.is_typing) {
                            typingIndicator.style.display = 'flex';
                        } else {
                            typingIndicator.style.display = 'none';
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Помилка при оновленні статусу користувача:', error);
            });
    }
}

/**
 * Перевіряємо, чи прокручений контейнер до кінця
 */
function isScrolledToBottom(element) {
    return element.scrollHeight - element.clientHeight <= element.scrollTop + 1;
}

/**
 * Прокручуємо контейнер до кінця
 */
function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

/**
 * Отримуємо значення cookie за іменем
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
