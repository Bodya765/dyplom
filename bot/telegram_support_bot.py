import os
import sys
import django
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from asgiref.sync import sync_to_async
from django.db.models import Q

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DJANGO_PROJECT_PATH = os.getenv("DJANGO_PROJECT_PATH")
DJANGO_SETTINGS_MODULE = os.getenv("DJANGO_SETTINGS_MODULE")

sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)

django.setup()

from announcements.models import SupportRequest

create_support_request = sync_to_async(SupportRequest.objects.create)
get_pending_requests = sync_to_async(SupportRequest.objects.filter)
update_request = sync_to_async(SupportRequest.objects.get)

CONTACT_ADMIN_BUTTON = "📞 Зв’язатися з адміністратором"
reply_keyboard = [[KeyboardButton(CONTACT_ADMIN_BUTTON)]]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот підтримки сайту VseOgolosha. Задавай своє питання, і я дам відповідь тобі на нього!\n\n"
        "Щоб задати питання адміністратору сайту скористайся кнопкою нижче або командою /admin",
        reply_markup=reply_markup
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши своє повідомлення для адміністратора, і я передам його!",
        reply_markup=reply_markup
    )
    context.user_data['awaiting_admin_message'] = True

async def check_admin_responses(context: ContextTypes.DEFAULT_TYPE):
    pending_requests = await get_pending_requests(
        Q(response__isnull=False) & Q(handled_by_admin=False) & Q(status='answered')
    )
    pending_requests = await sync_to_async(list)(pending_requests)

    for request in pending_requests:
        await context.bot.send_message(
            chat_id=request.user_id,
            text=f"Відповідь на питання: {request.question}\nВідповідь адміністратора: {request.response}",
            reply_markup=reply_markup
        )
        request.handled_by_admin = True
        await sync_to_async(request.save)()
    await asyncio.sleep(30)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    username = user.username or "Невідомий"
    message_text = update.message.text.lower().strip()

    if 'awaiting_admin_message' in context.user_data and context.user_data['awaiting_admin_message']:
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
            reply_markup=reply_markup
        )
        context.user_data['awaiting_admin_message'] = False
        return

    if message_text == CONTACT_ADMIN_BUTTON.lower():
        await update.message.reply_text(
            "Напиши своє повідомлення для адміністратора, і я передам його!",
            reply_markup=reply_markup
        )
        context.user_data['awaiting_admin_message'] = True
        return

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
        reply_markup=reply_markup
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(check_admin_responses, interval=30, first=0)
    app.run_polling()

if __name__ == "__main__":
    main()