// chat.js
let chatSocket = null;
let typingTimeout = null;

function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!token) {
        console.error('CSRF-токен не знайдено');
        return '';
    }
    return token.value;
}

function initializeChat(chatId, username) {
    // Ініціалізація WebSocket
    chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${chatId}/`);

    chatSocket.onopen = function(e) {
        console.log('WebSocket з’єднання відкрито');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('Отримано WebSocket-повідомлення:', data);
        if (data.type === 'message') {
            appendMessage(data, username);
        } else if (data.type === 'typing') {
            handleTypingIndicator(data, username);
        } else if (data.type === 'status') {
            updateUserStatus(data);
        } else if (data.type === 'edit_message') {
            console.log('Повідомлення успішно відредаговано:', data);
            updateEditedMessage(data);
        } else if (data.type === 'error') {
            console.error('Помилка WebSocket:', data.message);
            alert('Помилка при редагуванні: ' + data.message);
        }
    };

    chatSocket.onclose = function(e) {
        console.error('WebSocket закрито:', e);
        alert('З’єднання з чатом втрачено. Спробуйте оновити сторінку.');
    };

    chatSocket.onerror = function(e) {
        console.error('Помилка WebSocket:', e);
        alert('Виникла помилка з’єднання з чатом.');
    };

    // Обробка введення тексту (індикатор набору)
    const messageInput = document.getElementById('chat-message-input');
    messageInput.addEventListener('input', function() {
        if (chatSocket.readyState !== WebSocket.OPEN) {
            console.error('WebSocket не підключений');
            return;
        }
        clearTimeout(typingTimeout);
        chatSocket.send(JSON.stringify({
            'type': 'typing',
            'sender': username
        }));
        typingTimeout = setTimeout(() => {
            chatSocket.send(JSON.stringify({
                'type': 'typing',
                'sender': username,
                'stop': true
            }));
        }, 3000);
    });

    // Відправка повідомлення
    const submitButton = document.getElementById('chat-message-submit');
    submitButton.onclick = function() {
        sendMessage(chatId, username);
    };

    // Відправка повідомлення по натисканню Enter
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitButton.click();
        }
    });

    // Ініціалізація слухачів для кнопок редагування
    document.querySelectorAll('.edit-message-btn').forEach(button => {
        addEditMessageListener(button, chatId, username);
    });

    // Функція для додавання нового повідомлення
    function appendMessage(data, username) {
        const messagesDiv = document.getElementById('chat-messages');
        const messageDate = new Date(data.timestamp).toISOString().split('T')[0];
        let dateDivider = messagesDiv.querySelector(`.date-divider[data-date="${messageDate}"]`);

        if (!dateDivider) {
            dateDivider = document.createElement('div');
            dateDivider.classList.add('date-divider');
            dateDivider.setAttribute('data-date', messageDate);
            dateDivider.innerHTML = `<span>${new Date(data.timestamp).toLocaleDateString('uk-UA', { day: 'numeric', month: 'long', year: 'numeric' })}</span>`;
            messagesDiv.appendChild(dateDivider);
        }

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', data.sender === username ? 'sent' : 'received');
        messageDiv.setAttribute('data-message-id', data.message_id);

        if (data.sender !== username) {
            const senderSpan = document.createElement('span');
            senderSpan.classList.add('message-sender');
            senderSpan.textContent = data.sender;
            messageDiv.appendChild(senderSpan);
        }

        if (data.image) {
            const img = document.createElement('img');
            img.src = data.image;
            img.alt = 'Фото';
            img.classList.add('message-image');
            messageDiv.appendChild(img);
        }

        if (data.message) {
            const contentP = document.createElement('p');
            contentP.classList.add('message-content');
            contentP.textContent = data.message;
            messageDiv.appendChild(contentP);
        }

        const metaDiv = document.createElement('div');
        metaDiv.classList.add('message-meta');

        const timestampSpan = document.createElement('span');
        timestampSpan.classList.add('message-timestamp');
        timestampSpan.textContent = new Date(data.timestamp).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
        metaDiv.appendChild(timestampSpan);

        if (data.sender === username) {
            const actionsSpan = document.createElement('span');
            actionsSpan.classList.add('message-actions');
            const editButton = document.createElement('button');
            editButton.classList.add('edit-message-btn');
            editButton.setAttribute('data-message-id', data.message_id);
            editButton.textContent = 'Редагувати';
            actionsSpan.appendChild(editButton);
            metaDiv.appendChild(actionsSpan);

            const statusSpan = document.createElement('span');
            statusSpan.classList.add('message-status');
            const ticksSpan = document.createElement('span');
            ticksSpan.classList.add(data.is_read ? 'read-ticks' : 'unread-ticks');
            ticksSpan.textContent = '✔✔';
            statusSpan.appendChild(ticksSpan);

            if (data.is_read && data.read_at) {
                const readAtSpan = document.createElement('span');
                readAtSpan.classList.add('message-read-at');
                readAtSpan.textContent = `(Прочитано ${new Date(data.read_at).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })})`;
                statusSpan.appendChild(readAtSpan);
            }

            metaDiv.appendChild(statusSpan);

            addEditMessageListener(editButton, chatId, username);
        }

        messageDiv.appendChild(metaDiv);
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // Обробка індикатора набору тексту
    function handleTypingIndicator(data, username) {
        const typingIndicator = document.getElementById('typing-indicator');
        if (data.sender !== username && !data.stop) {
            typingIndicator.style.display = 'inline';
            setTimeout(() => {
                typingIndicator.style.display = 'none';
            }, 3000);
        } else {
            typingIndicator.style.display = 'none';
        }
    }

    // Оновлення статусу користувача
    function updateUserStatus(data) {
        const statusElements = document.querySelectorAll(`.chat-item-status[data-username="${data.username}"]`);
        statusElements.forEach(element => {
            element.textContent = data.is_online ? 'Онлайн' : 'Офлайн';
            element.classList.toggle('online', data.is_online);
        });
    }

    // Оновлення відредагованого повідомлення
    function updateEditedMessage(data) {
        const messageDiv = document.querySelector(`.message[data-message-id="${data.message_id}"]`);
        if (messageDiv) {
            let contentP = messageDiv.querySelector('.message-content');
            if (!contentP && data.content) {
                contentP = document.createElement('p');
                contentP.classList.add('message-content');
                messageDiv.insertBefore(contentP, messageDiv.querySelector('.message-meta'));
            }
            if (contentP) {
                contentP.textContent = data.content;
            }

            let editedSpan = messageDiv.querySelector('.message-edited');
            if (!editedSpan) {
                editedSpan = document.createElement('span');
                editedSpan.classList.add('message-edited');
                messageDiv.querySelector('.message-meta').insertBefore(editedSpan, messageDiv.querySelector('.message-timestamp').nextSibling);
            }
            editedSpan.textContent = `(редаговано ${new Date(data.edited_at).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })}))`;
        }
    }

    // Відправка повідомлення
    function sendMessage(chatId, username) {
        const messageInput = document.getElementById('chat-message-input');
        const message = messageInput.value.trim();
        const imageInput = document.getElementById('chat-image-input');
        const imageFile = imageInput.files[0];

        if (!message && !imageFile) {
            alert('Повідомлення не може бути порожнім');
            return;
        }

        if (imageFile && imageFile.size > 5 * 1024 * 1024) {
            alert('Зображення занадто велике (максимум 5 МБ)');
            return;
        }

        if (chatSocket.readyState !== WebSocket.OPEN) {
            alert('З’єднання з чатом втрачено. Спробуйте оновити сторінку.');
            return;
        }

        const formData = new FormData();
        formData.append('chat_id', chatId);
        formData.append('content', message);
        if (imageFile) {
            formData.append('image', imageFile);
        }

        fetch('/chat/send_message/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                chatSocket.send(JSON.stringify({
                    'type': 'message',
                    'message': data.content || '',
                    'image': data.image_url || null,
                    'sender': username,
                    'timestamp': new Date().toISOString(),
                    'message_id': data.message_id,
                    'is_read': false
                }));
                messageInput.value = '';
                imageInput.value = '';
            } else {
                alert('Помилка при відправці повідомлення: ' + (data.error || 'Невідома помилка'));
            }
        })
        .catch(error => {
            console.error('Помилка:', error);
            alert('Помилка при відправці повідомлення');
        });
    }

    // Обробка редагування повідомлення
    function addEditMessageListener(button, chatId, username) {
        if (!button) return;

        button.addEventListener('click', function() {
            const messageId = this.getAttribute('data-message-id');
            console.log('Натиснуто "Редагувати" для messageId:', messageId);
            const messageDiv = document.querySelector(`.message[data-message-id="${messageId}"]`);
            const contentP = messageDiv.querySelector('.message-content');
            const content = contentP ? contentP.textContent : '';

            const modal = document.getElementById('edit-message-modal');
            const input = document.getElementById('edit-message-input');
            input.value = content;
            modal.style.display = 'flex';

            const saveButton = document.getElementById('save-edit-message');
            const closeButton = document.getElementById('close-edit-modal');

            saveButton.onclick = function() {
                const newContent = input.value.trim();
                if (!newContent) {
                    alert('Повідомлення не може бути порожнім');
                    return;
                }

                if (chatSocket.readyState !== WebSocket.OPEN) {
                    alert('З’єднання з чатом втрачено. Спробуйте оновити сторінку.');
                    return;
                }

                if (!messageId) {
                    console.error('Невірний messageId:', messageId);
                    alert('Помилка: некоректний ідентифікатор повідомлення');
                    return;
                }

                const editedAt = new Date().toISOString();
                const message = {
                    'type': 'edit_message',
                    'message_id': messageId,
                    'content': newContent,
                    'edited_at': editedAt
                };
                console.log('Відправляємо WebSocket-повідомлення для редагування:', message);
                chatSocket.send(JSON.stringify(message));
                modal.style.display = 'none';
            };

            closeButton.onclick = function() {
                modal.style.display = 'none';
            };
        });
    }
}