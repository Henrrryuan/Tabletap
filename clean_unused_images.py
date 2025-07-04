import os
import django
import shutil
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tabletap.settings')
django.setup()

from core.models import MenuItem

# 创建备份目录
backup_dir = f'media/menu_items_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
os.makedirs(backup_dir, exist_ok=True)
print(f'已创建备份目录: {backup_dir}')

# 获取数据库中引用的图片
used_images = []
for item in MenuItem.objects.all():
    if item.image and item.image.name:
        used_images.append(item.image.name)

print(f'数据库中引用的图片: {len(used_images)}')
for img in used_images:
    print(f' - {img}')

# 获取media/menu_items目录中的所有图片
media_dir = 'media/menu_items'
all_images = []
for root, dirs, files in os.walk(media_dir):
    for file in files:
        if file.startswith('.'):
            continue  # 跳过隐藏文件
        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, 'media')
        all_images.append(rel_path)

print(f'\n媒体目录中的图片总数: {len(all_images)}')

# 找出未使用的图片
unused_images = [img for img in all_images if img not in used_images]
print(f'未使用的图片数量: {len(unused_images)}')

# 备份并删除未使用的图片
for img_path in unused_images:
    full_path = os.path.join('media', img_path)
    backup_path = os.path.join(backup_dir, os.path.basename(full_path))
    
    # 复制到备份目录
    shutil.copy2(full_path, backup_path)
    
    # 删除原文件
    os.remove(full_path)
    print(f'已备份并删除: {img_path}')

print(f'\n清理完成！所有未使用的图片已备份到 {backup_dir} 并从原位置删除') 