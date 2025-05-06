import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import os
import mysql.connector
from .models import User, Question, Answer
import ollama

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Завантаження змінних середовища
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID')
ADMIN_NICKNAME = os.getenv('ADMIN_NICKNAME')

# Стани для ConversationHandler
NAME, ANSWER = range(2)

# Ініціалізація бази даних MySQL
def init_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
        conn.close()
        logger.info("База даних ініціалізована успішно")
    except Exception as e:
        logger.error(f"Помилка ініціалізації бази даних: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Отримано команду /start від користувача {update.effective_chat.id}")
    user_id = update.effective_chat.id
    try:
        user = User.objects.get(chat_id=user_id)
        await update.message.reply_text(f"Вітаю, {user.name}! Задавайте питання щодо VseOgolosha.")
        return ConversationHandler.END
    except User.DoesNotExist:
        await update.message.reply_text("Вітаю! Введіть ваше ім'я:")
        return NAME

# Обробка імені користувача
async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_chat.id
    name = update.message.text.strip()
    User.objects.create(chat_id=user_id, name=name)
    await update.message.reply_text(f"Реєстрація успішна, {name}! Задавайте питання щодо VseOgolosha.")
    return ConversationHandler.END

# Обробка текстових повідомлень (питань)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    text = update.message.text
    logger.info(f"Отримано повідомлення від {user_id}: {text}")

    try:
        user = User.objects.get(chat_id=user_id)
    except User.DoesNotExist:
        await update.message.reply_text("Будь ласка, зареєструйтесь за допомогою /start.")
        return

    question = Question.objects.create(user=user, text=text)

    try:
        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'system',
                'content': (
                    'Ви — бот підтримки сайту VseOgolosha, відповідайте українською. '
                    'Категорії: Транспорт, Нерухомість, Електроніка, Одяг, Меблі, Книги, '
                    'Віддам безкоштовно, Товари для геймерів, Спорт і хобі, Тварини. '
                    'FAQ: Як створити оголошення? Перейдіть до /announcement/create/. '
                    'Як зв’язатися з продавцем? Використовуйте контактну форму на сторінці оголошення.'
                )
            },
            {'role': 'user', 'content': text}
        ])
        answer_text = response['message']['content']

        if len(answer_text) > 20 and not any(phrase in answer_text.lower() for phrase in ['не знаю', 'немає інформації']):
            Answer.objects.create(question=question, text=answer_text)
            question.answered = True
            question.save()
            await update.message.reply_text(answer_text)
        else:
            raise ValueError("Недостатньо якісна відповідь")
    except Exception as e:
        logger.error(f"Помилка LLaMA: {e}")
        Answer.objects.create(
            question=question,
            text=f"Не можу відповісти. Зв’яжіться з адміністратором: {ADMIN_NICKNAME}"
        )
        question.answered = True
        question.save()
        await update.message.reply_text(f"Не можу відповісти. Зв’яжіться з адміністратором: {ADMIN_NICKNAME}")

        keyboard = [[InlineKeyboardButton("Відповісти", callback_data=f"answer_{question.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=f"Нове питання від {user.name} (ID: {user_id}):\n{text}",
            reply_markup=reply_markup
        )

# Обробка натискання кнопки "Відповісти"
async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    question_id = int(query.data.split('_')[1])
    context.user_data['question_id'] = question_id
    await query.message.reply_text("Введіть вашу відповідь:")
    return ANSWER

# Збереження відповіді адміністратора
async def save_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    question_id = context.user_data['question_id']
    answer_text = update.message.text
    question = Question.objects.get(id=question_id)
    Answer.objects.create(question=question, text=answer_text, is_admin=True)
    question.answered = True
    question.save()
    await context.bot.send_message(
        chat_id=question.user.chat_id,
        text=f"Відповідь адміністратора:\n{answer_text}"
    )
    await update.message.reply_text("Відповідь надіслано користувачу.")
    return ConversationHandler.END

# Основна функція запуску бота
async def main():
    init_db()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_answer)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(answer_question, pattern='^answer_'))

    logger.info("Запуск бота...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())