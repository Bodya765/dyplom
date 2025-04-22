import aiohttp
import os
import asyncio
from dotenv import load_dotenv

# Завантажуємо .env
load_dotenv()

OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

async def get_ollama_response(user_message, chat_history=None):
    faq = """
    Питання: Чому мій акаунт заблокований?
    Відповідь: Твій акаунт могли заблокувати через порушення правил платформи, наприклад, якщо ти розмістив заборонений товар. Напиши в підтримку, щоб дізнатися деталі!

    Питання: Як зв’язатися з продавцем?
    Відповідь: Відкрий оголошення, яке тобі сподобалося, і натисни на кнопку "Зв"язатися з продавцем". Ти зможеш поспілкуватися прямо в чаті!

    Питання: Чому моє оголошення не опубліковане?
    Відповідь: Можливо, ти не заповнив усі потрібні поля, або оголошення ще перевіряють модератори. Перевір, чи все заповнено, і зачекай трохи!

    Питання: Як змінити пароль?
    Відповідь: Зайди в налаштування свого профілю, вибери "Змінити пароль", введи новий пароль
    """
    print(f"Формуємо запит до Ollama для повідомлення: {user_message}")
    try:
        messages = f"Ти чат-бот-помічник. Відповідай ВИКЛЮЧНО українською мовою, у дружньому розмовному стилі, як спілкуються українці щодня. НЕ використовуй англійські, російські чи інші мови. Уникай кальок (наприклад, не кажи 'гайтувати', а кажи 'не соромся'), формальних фраз чи дивних слів. Будь привітним і природним, ніби розмовляєш із другом. Використовуй лише ці дані:\n{faq}\nЯкщо відповідь не знайдена, скажи: 'Ой, не знаю такого, краще звернися до підтримки!'\n"
        messages += f"Користувач: {user_message}\nБот: "
        print(f"Надсилаємо запит до Ollama: {messages[:100]}...")

        async with aiohttp.ClientSession() as session:
            print(f"Виконуємо HTTP-запит до {OLLAMA_HOST}/api/generate")
            async with session.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": "gemma2:9b",
                    "prompt": messages,
                    "stream": False
                },
                timeout=60
            ) as response:
                print(f"Статус відповіді від Ollama: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Помилка HTTP: {response.status}, текст помилки: {error_text}")
                    return f"Виникла помилка: сервер Ollama повернув статус {response.status}. Текст помилки: {error_text}"
                data = await response.json()
                print(f"Отримана відповідь від Ollama: {data.get('response')}")
                if "response" not in data:
                    print(f"Повна відповідь від Ollama: {data}")
                    return "Виникла помилка: відповідь від Ollama не містить поля 'response'."
                return data["response"]
    except aiohttp.ClientConnectorError as e:
        print(f"Помилка підключення до Ollama: {str(e)}")
        return "Виникла помилка: не вдалося підключитися до сервера Ollama. Переконайся, що Ollama запущена."
    except asyncio.TimeoutError as e:
        print(f"Тайм-аут запиту до Ollama: {str(e)}")
        return "Виникла помилка: сервер Ollama не відповів вчасно."
    except aiohttp.ClientResponseError as e:
        print(f"Помилка відповіді від Ollama: {str(e)}")
        return f"Виникла помилка: {str(e)}"
    except Exception as e:
        print(f"Інша помилка в get_ollama_response: {str(e)}")
        return f"Виникла помилка: {str(e)}"