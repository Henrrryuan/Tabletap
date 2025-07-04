from django.db import migrations
from decimal import Decimal

def create_sample_menu_items(apps, schema_editor):
    Menu = apps.get_model('core', 'Menu')
    MenuItem = apps.get_model('core', 'MenuItem')
    Category = apps.get_model('core', 'Category')
    
    # 创建默认菜单
    default_menu = Menu.objects.create(
        name='标准菜单',
        description='我们的标准菜单',
        is_active=True
    )
    
    # 获取所有分类
    categories = {cat.name: cat for cat in Category.objects.all()}
    
    # 示例菜品数据
    sample_items = [
        {
            'name': '扬州炒饭',
            'description': '精选食材，传统工艺',
            'price': Decimal('28.00'),
            'category': categories['主食'],
            'is_available': True
        },
        {
            'name': '宫保鸡丁',
            'description': '麻辣鲜香，回味无穷',
            'price': Decimal('38.00'),
            'category': categories['热菜'],
            'is_available': True
        },
        {
            'name': '凉拌黄瓜',
            'description': '清脆爽口，开胃佳品',
            'price': Decimal('18.00'),
            'category': categories['凉菜'],
            'is_available': True
        },
        {
            'name': '可乐',
            'description': '冰镇可口可乐',
            'price': Decimal('6.00'),
            'category': categories['饮品'],
            'is_available': True
        },
        {
            'name': '芒果布丁',
            'description': '香甜可口，细腻顺滑',
            'price': Decimal('15.00'),
            'category': categories['甜点'],
            'is_available': True
        }
    ]
    
    # 创建菜品
    for item_data in sample_items:
        category = item_data.pop('category')
        menu_item = MenuItem.objects.create(
            menu=default_menu,
            category=category,
            **item_data
        )

def delete_sample_menu_items(apps, schema_editor):
    Menu = apps.get_model('core', 'Menu')
    Menu.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_default_categories'),
    ]

    operations = [
        migrations.RunPython(create_sample_menu_items, delete_sample_menu_items),
    ] 