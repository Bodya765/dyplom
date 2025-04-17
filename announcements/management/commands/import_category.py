import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from announcements.models import Category

class Command(BaseCommand):
    help = 'Імпортує назви категорій з JSON-файлу в базу даних'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Шлях до JSON-файлу з категоріями')
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистити всі існуючі категорії перед імпортом'
        )

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        clear = options['clear']

        try:
            # Очистка існуючих категорій, якщо вказано --clear
            if clear:
                Category.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("Усі існуючі категорії видалено"))

            # Читання JSON-файлу
            with open(json_file_path, 'r', encoding='utf-8') as file:
                categories_data = json.load(file)

            # Перевірка, чи categories_data є списком
            if not isinstance(categories_data, list):
                self.stdout.write(self.style.ERROR("JSON-файл має містити список категорій"))
                return

            for category_data in categories_data:
                name = category_data.get('name')
                category_id = category_data.get('id')

                if not name:
                    self.stdout.write(self.style.ERROR(f"Пропущено категорію: відсутнє поле 'name'"))
                    continue

                # Створення або оновлення категорії
                defaults = {'name': name, 'slug': slugify(name)}
                if category_id:
                    # Якщо ID вказано, оновлюємо або створюємо запис із заданим ID
                    try:
                        category, created = Category.objects.get_or_create(
                            id=category_id,
                            defaults=defaults
                        )
                        if not created:
                            # Оновлюємо існуючий запис
                            Category.objects.filter(id=category_id).update(**defaults)
                            category = Category.objects.get(id=category_id)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Помилка при створенні категорії з ID {category_id}: {str(e)}"))
                        continue
                else:
                    # Якщо ID не вказано, створюємо новий запис
                    category, created = Category.objects.get_or_create(
                        name=name,
                        defaults={'slug': slugify(name)}
                    )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Додано категорію: {category.name} (ID: {category.id}, slug: {category.slug})"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Категорія {category.name} вже існує (ID: {category.id}, slug: {category.slug})"
                    ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Файл {json_file_path} не знайдено"))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR("Помилка при розборі JSON-файлу"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Виникла помилка: {str(e)}"))