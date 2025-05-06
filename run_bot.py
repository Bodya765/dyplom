import os
import django
import asyncio
from support.bot import main

# Налаштування Django перед імпортом моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Якщо цикл уже запущений, додаємо завдання
            loop.create_task(main())
        else:
            # Якщо цикл не запущений, запускаємо його
            loop.run_until_complete(main())
    except RuntimeError as e:
        # Створюємо новий цикл, якщо get_event_loop() повернув закритий цикл
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())