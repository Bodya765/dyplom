from django.db import migrations
from django.utils.text import slugify

def add_categories(apps, schema_editor):
    Category = apps.get_model('announcements', 'Category')

    def create_category(name):
        slug = slugify(name)
        if not Category.objects.filter(name=name).exists():
            return Category.objects.create(name=name, slug=slug)
        return Category.objects.get(name=name)

    create_category('Транспорт - Легкові авто')
    create_category('Транспорт - Вантажівки')
    create_category('Транспорт - Мотоцикли')
    create_category('Нерухомість - Квартири - Продаж')
    create_category('Нерухомість - Квартири - Довгострокова оренда')
    create_category('Нерухомість - Квартири - Подобова або погодинна оренда')
    create_category('Нерухомість - Будинки - Продаж')
    create_category('Нерухомість - Будинки - Довгострокова оренда')
    create_category('Нерухомість - Будинки - Подобова або погодинна оренда')
    create_category('Нерухомість - Кімнати - Продаж')
    create_category('Нерухомість - Кімнати - Довгострокова оренда')
    create_category('Нерухомість - Кімнати - Подобова або погодинна оренда')

    create_category('Одяг - Чоловічий одяг')
    create_category('Одяг - Жіночий одяг')
    create_category('Одяг - Дитячий одяг')
    create_category('Електроніка')
    create_category('Меблі')
    create_category('Книги')
    create_category('Віддам безкоштовно')
    create_category('Товари для геймерів')
    create_category('Спорт і хобі')
    create_category('Тварини')

class Migration(migrations.Migration):
    dependencies = [
        ('announcements', '0004_delete_chat'),
    ]

    operations = [
        migrations.RunPython(add_categories),
    ]