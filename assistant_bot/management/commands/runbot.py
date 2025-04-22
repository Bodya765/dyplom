from django.core.management.base import BaseCommand
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from assistant_bot.models import ChatMessage
from assistant_bot.utils import get_ollama_response
import os
from dotenv import load_dotenv
from asgiref.sync import sync_to_async

class Command(BaseCommand):
    help = 'Runs the Telegram assistant bot'

    def handle(self, *args, app=None, **options):
        # Завантажуємо .env
        load_dotenv()

        if app is None:
            token = os.getenv('TELEGRAM_TOKEN')
            if not token:
                self.stdout.write(self.style.ERROR('TELEGRAM_TOKEN not found in .env file'))
                return
            app = Application.builder().token(token).build()

        self.admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        if not self.admin_chat_id:
            self.stdout.write(self.style.ERROR('ADMIN_CHAT_ID not found in .env file'))
            return

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            reply_keyboard = [
                ['Чому мій акаунт заблокований?', 'Як зв’язатися з продавцем?'],
                ['Чому моє оголошення не опубліковане?', 'Як змінити пароль?']
            ]
            self.stdout.write(self.style.SUCCESS(f"Користувач {update.message.from_user.id} натиснув /start"))
            await update.message.reply_text(
                "Привіт! Я твій помічник. Як можу допомогти?",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            )

        async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = str(update.message.from_user.id)
            user_message = update.message.text
            self.stdout.write(self.style.SUCCESS(f"Отримано повідомлення від {user_id}: {user_message}"))

            # Якщо це адмін, який відповідає у форматі user_id: відповідь
            if str(update.message.chat_id) == self.admin_chat_id and ":" in user_message:
                self.stdout.write(self.style.SUCCESS(f"Адмін відповідає у форматі: {user_message}"))
                target_user_id, admin_response = user_message.split(":", 1)
                target_user_id = target_user_id.strip()
                admin_response = admin_response.strip()

                self.stdout.write(self.style.SUCCESS(f"Надсилаємо відповідь користувачу {target_user_id}: {admin_response}"))
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"Оператор: {admin_response}"
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Помилка при надсиланні відповіді користувачу {target_user_id}: {str(e)}"))
                    await update.message.reply_text(f"Помилка: не вдалося надіслати відповідь користувачу {target_user_id}")
                    return

                self.stdout.write(self.style.SUCCESS(f"Зберігаємо відповідь оператора для {target_user_id}"))
                try:
                    await sync_to_async(ChatMessage.objects.create)(
                        user_id=target_user_id,
                        message="Оператор відповідає",
                        response=f"Оператор: {admin_response}"
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Помилка при збереженні відповіді оператора: {str(e)}"))
                    await update.message.reply_text("Помилка при збереженні відповіді оператора.")
                    return

                await update.message.reply_text(f"Відповідь надіслана користувачу {target_user_id}")
                self.stdout.write(self.style.SUCCESS(f"Адмін успішно відповів користувачу {target_user_id}"))
                return

            # Обробляємо як звичайне повідомлення
            self.stdout.write(self.style.SUCCESS(f"Обробляємо повідомлення від {user_id}"))

            # Отримуємо історію чату
            self.stdout.write(self.style.SUCCESS(f"Отримуємо історію чату для {user_id}"))
            try:
                chat_history = await sync_to_async(list)(
                    ChatMessage.objects.filter(user_id=user_id).order_by('-timestamp')
                )
                self.stdout.write(self.style.SUCCESS(f"Історія чату отримана: {len(chat_history)} записів"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Помилка при отриманні історії чату: {str(e)}"))
                await update.message.reply_text("Виникла помилка при отриманні історії чату. Спробуй ще раз!")
                return

            # Отримуємо відповідь від Ollama
            self.stdout.write(self.style.SUCCESS(f"Запит до Ollama: {user_message}"))
            try:
                response = await get_ollama_response(user_message, chat_history)
                self.stdout.write(self.style.SUCCESS(f"Відповідь від Ollama: {response}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Помилка при отриманні відповіді від Ollama: {str(e)}"))
                response = "Виникла помилка: не вдалося отримати відповідь. Спробуй ще раз!"
                await update.message.reply_text(response)
                return

            # Зберігаємо повідомлення
            self.stdout.write(self.style.SUCCESS(f"Зберігаємо повідомлення для {user_id}"))
            try:
                await sync_to_async(ChatMessage.objects.create)(
                    user_id=user_id,
                    message=user_message,
                    response=response
                )
                self.stdout.write(self.style.SUCCESS(f"Повідомлення збережено"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Помилка при збереженні повідомлення: {str(e)}"))
                await update.message.reply_text("Виникла помилка при збереженні повідомлення. Спробуй ще раз!")
                return

            # Якщо відповідь не знайдена, надсилаємо повідомлення адміну
            if "Ой, не знаю такого, краще звернися до підтримки!" in response:
                self.stdout.write(self.style.SUCCESS(f"Відповідь не знайдена, надсилаємо повідомлення адміну"))
                await context.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=f"Користувач {user_id} надіслав запит: '{user_message}'.\nНапиши відповідь у форматі: {user_id}: твоя_відповідь"
                )
                await update.message.reply_text(
                    "Ой, не знаю такого! Твій запит передано оператору, чекай на відповідь у цьому чаті!"
                )
            else:
                self.stdout.write(self.style.SUCCESS(f"Надсилаємо відповідь користувачу: {response}"))
                await update.message.reply_text(response)

        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            self.stdout.write(self.style.ERROR(f"Update {update} caused error {context.error}"))
            if update and update.message:
                await update.message.reply_text("Виникла помилка, спробуй ще раз!")

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_error_handler(error_handler)

        if not args:
            self.stdout.write(self.style.SUCCESS('Starting Telegram bot...'))
            app.run_polling()