import json
from django.core.management.base import BaseCommand
from announcements.models import Location

class Command(BaseCommand):
    help = 'Імпорт міст з JSON-файлу в базу даних'

    def handle(self, *args, **kwargs):
        json_path = 'announcements/static/locations/locations.json'

        try:
            with open(json_path, encoding='utf-8') as file:
                data = json.load(file)

            Location.objects.all().delete()  # Очистка таблиці перед імпортом

            locations = [Location(name=item["name"], district=item["district"]) for item in data]
            Location.objects.bulk_create(locations)

            self.stdout.write(self.style.SUCCESS(f"Успішно імпортовано {len(locations)} міст"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Помилка імпорту: {e}"))
