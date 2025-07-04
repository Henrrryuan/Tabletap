from django.db import migrations

def create_default_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    default_categories = [
        {
            'name': '主食',
            'description': '米饭、面食等主食类',
        },
        {
            'name': '热菜',
            'description': '各类炒菜、煲汤等热菜',
        },
        {
            'name': '凉菜',
            'description': '各类凉拌菜、前菜等',
        },
        {
            'name': '饮品',
            'description': '各类饮料、酒水等',
        },
        {
            'name': '甜点',
            'description': '各类甜品、水果等',
        },
    ]
    
    for category_data in default_categories:
        Category.objects.create(**category_data)

def delete_default_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    Category.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, delete_default_categories),
    ] 