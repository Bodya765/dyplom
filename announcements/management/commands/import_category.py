import json
from django.core.management.base import BaseCommand
from announcements.models import Category

class Command(BaseCommand):
    help = 'Імпортує назви категорій з JSON-файлу в базу даних'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Шлях до JSON-файлу з категоріями')

    def handle(self, *args, **options):
        json_file_path = options['json_file']

        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                categories_data = json.load(file)

            for category_data in categories_data:
                name = category_data.get('name')

                if not name:
                    self.stdout.write(self.style.ERROR(f"Пропущено категорію: відсутнє поле 'name'"))
                    continue

                category, created = Category.objects.get_or_create(
                    name=name
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Додано категорію: {category.name} (slug: {category.slug})"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Категорія {category.name} вже існує (slug: {category.slug})"
                    ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Файл {json_file_path} не знайдено"))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR("Помилка при розборі JSON-файлу"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Виникла помилка: {str(e)}"))