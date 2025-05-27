import os
import sys
import django
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from asgiref.sync import sync_to_async
from django.db.models import Q
from openai import OpenAI

# Завантаження змінних середовища
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DJANGO_PROJECT_PATH = os.getenv("DJANGO_PROJECT_PATH")
DJANGO_SETTINGS_MODULE = os.getenv("DJANGO_SETTINGS_MODULE")

# Налаштування Django
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
django.setup()

# Імпорт моделі Django
from announcements.models import SupportRequest

# Асинхронні функції для роботи з Django
create_support_request = sync_to_async(SupportRequest.objects.create)
get_pending_requests = sync_to_async(SupportRequest.objects.filter)
update_request = sync_to_async(SupportRequest.objects.get)

# Налаштування OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Кнопки
CONTACT_ADMIN_BUTTON = "📞 Зв’язатися з адміністратором"
SATISFIED_BUTTON = "✅ Дякую, відповідь підходить"
REPLY_KEYBOARD = [[KeyboardButton(CONTACT_ADMIN_BUTTON)]]
REPLY_MARKUP = ReplyKeyboardMarkup(REPLY_KEYBOARD, resize_keyboard=True)
INLINE_KEYBOARD = [
    [InlineKeyboardButton(SATISFIED_BUTTON, callback_data="satisfied")],
    [InlineKeyboardButton(CONTACT_ADMIN_BUTTON, callback_data="contact_admin")]
]
INLINE_MARKUP = InlineKeyboardMarkup(INLINE_KEYBOARD)

# Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот підтримки сайту VseOgolosha. Задавай своє питання, і я постараюся відповісти!\n\n"
        "Якщо відповідь тобі не підійде, ти зможеш звернутися до адміністратора за допомогою кнопки нижче або команди /admin.",
        reply_markup=REPLY_MARKUP
    )

# Команда для прямого звернення до адміністратора
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши своє повідомлення для адміністратора, і я передам його!",
        reply_markup=REPLY_MARKUP
    )
    context.user_data['awaiting_admin_message'] = True

# Функція для генерації відповіді від AI
async def get_ai_response(question: str) -> str:
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти бот підтримки сайту оголошень VseOgolosha. Відповідай коротко, чітко і по суті."},
                    {"role": "user", "content": question}
                ],
                max_tokens=150,
                temperature=0.7
            )
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Виникла помилка при генерації відповіді: {str(e)}"

# Періодична перевірка відповідей адміністратора
async def check_admin_responses(context: ContextTypes.DEFAULT_TYPE):
    pending_requests = await get_pending_requests(
        Q(response__isnull=False) & Q(handled_by_admin=False) & Q(status='answered')
    )
    pending_requests = await sync_to_async(list)(pending_requests)

    for request in pending_requests:
        await context.bot.send_message(
            chat_id=request.user_id,
            text=f"Відповідь на питання: {request.question}\nВідповідь адміністратора: {request.response}",
            reply_markup=REPLY_MARKUP
        )
        request.handled_by_admin = True
        await sync_to_async(request.save)()
    await asyncio.sleep(30)

# Обробка натискання на inline-кнопки
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "satisfied":
        await query.message.reply_text(
            "Радий, що зміг допомогти! Якщо будуть інші питання, пиши!",
            reply_markup=REPLY_MARKUP
        )
        # Очищаємо збережене питання
        if 'last_question' in context.user_data:
            del context.user_data['last_question']
    elif query.data == "contact_admin":
        if 'last_question' in context.user_data:
            user = query.message.chat
            user_id = str(user.id)
            username = user.username or "Невідомий"
            question = context.user_data['last_question']

            # Створюємо запит до адміністратора
            support_request = await create_support_request(
                user_id=user_id,
                username=username,
                question=question,
                status="pending",
                handled_by_admin=False
            )

            admin_keyboard = [
                [InlineKeyboardButton("Переглянути в адмін-панелі", url="http://127.0.0.1:8000/admin-panel/")]
            ]
            admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)

            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"Запит #{support_request.id} від @{username} (ID: {user_id}):\n{question}",
                reply_markup=admin_reply_markup
            )

            await query.message.reply_text(
                f"Твоє повідомлення надіслане адміністратору ({ADMIN_USERNAME})! Очікуй відповіді.",
                reply_markup=REPLY_MARKUP
            )
            # Очищаємо збережене питання
            del context.user_data['last_question']
        else:
            await query.message.reply_text(
                "Не вдалося знайти твоє останнє питання. Будь ласка, напиши його ще раз.",
                reply_markup=REPLY_MARKUP
            )
            context.user_data['awaiting_admin_message'] = True

# Обробка текстових повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    message_text = update.message.text.strip()

    # Якщо користувач очікує написання повідомлення для адміністратора
    if 'awaiting_admin_message' in context.user_data and context.user_data['awaiting_admin_message']:
        user_id = str(user.id)
        username = user.username or "Невідомий"

        support_request = await create_support_request(
            user_id=user_id,
            username=username,
            question=message_text,
            status="pending",
            handled_by_admin=False
        )

        admin_keyboard = [
            [InlineKeyboardButton("Переглянути в адмін-панелі", url="http://127.0.0.1:8000/admin-panel/")]
        ]
        admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Запит #{support_request.id} від @{username} (ID: {user_id}):\n{message_text}",
            reply_markup=admin_reply_markup
        )

        await update.message.reply_text(
            f"Твоє повідомлення надіслане адміністратору ({ADMIN_USERNAME})! Очікуй відповіді.",
            reply_markup=REPLY_MARKUP
        )
        context.user_data['awaiting_admin_message'] = False
        return

    # Зберігаємо питання для можливого звернення до адміністратора
    context.user_data['last_question'] = message_text

    # Відповідь від AI
    ai_response = await get_ai_response(message_text)
    await update.message.reply_text(
        f"Відповідь: {ai_response}\n\nЧи підійшла тобі ця відповідь?",
        reply_markup=INLINE_MARKUP
    )

# Головна функція
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.job_queue.run_repeating(check_admin_responses, interval=30, first=0)
    app.run_polling()

if __name__ == "__main__":
    main()