import os
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from assistant_bot.management.commands.runbot import Command as BotCommand
from dotenv import load_dotenv

# Завантажуємо .env
load_dotenv()

@csrf_exempt
async def telegram_webhook(request):
    # Ініціалізація Application у функції, а не на рівні модуля
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not found in .env file")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    bot_command = BotCommand()
    bot_command.handle(app=app)

    update = Update.de_json(request.body.decode('utf-8'), app.bot)
    await app.process_update(update)
    return HttpResponse(status=200)