from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import os
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, verbose_name='Category Image')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Menu(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True, verbose_name='Menu Image')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        # 删除关联的图片文件
        if self.image:
            # 保存图片路径以便后续删除
            image_path = self.image.path
            # 检查文件是否存在
            if os.path.isfile(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting image file for {self.name}: {str(e)}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.image:
            try:
                # 打开图片
                img = Image.open(self.image)
                
                # 转换为RGB模式（处理RGBA等其他格式）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 设置固定尺寸（1:1比例）
                target_size = (800, 800)
                
                # 创建一个新的正方形图片对象，背景为白色
                new_img = Image.new('RGB', target_size, 'white')
                
                # 计算缩放比例
                ratio = min(target_size[0] / img.width, target_size[1] / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                
                # 调整原图尺寸，保持比例
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 计算居中位置
                x = (target_size[0] - new_width) // 2
                y = (target_size[1] - new_height) // 2
                
                # 将调整后的图片粘贴到新图片的中心
                new_img.paste(img, (x, y))
                
                # 保存处理后的图片
                output = BytesIO()
                new_img.save(output, format='JPEG', quality=95)
                output.seek(0)
                
                # 更新图片字段
                self.image = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    f"{self.image.name.split('.')[0]}.jpg",
                    'image/jpeg',
                    sys.getsizeof(output),
                    None
                )
            except Exception as e:
                print(f"Error processing image for {self.name}: {str(e)}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.menu.name}"

class Table(models.Model):
    number = models.CharField(max_length=10, unique=True, verbose_name='Table Number')
    number_int = models.IntegerField(verbose_name='Table Number Value', null=True, blank=True)
    seats = models.IntegerField(verbose_name='Number of Seats')
    is_occupied = models.BooleanField(default=False, verbose_name='Is Occupied')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True, verbose_name='QR Code')
    last_order_time = models.DateTimeField(null=True, blank=True, verbose_name='Last Order Time')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    def __str__(self):
        return f'Table {self.number} ({self.seats} seats)'

    def generate_qr_code(self):
        # 获取当前站点域名

        domain = 'infs3202-183b16dd.uqcloud.net'

        # 生成菜单URL（包含桌号参数）
        menu_url = f'http://{domain}{reverse("table_menu", args=[self.number])}'
        

        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(menu_url)
        qr.make(fit=True)

        # 创建图片
        img = qr.make_image(fill_color="black", back_color="white")

        # 保存路径
        file_name = f'table_{self.number}.png'
        file_path = os.path.join('qrcodes', file_name)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 保存图片
        img.save(full_path)
        self.qr_code = file_path
        self.save()

    def save(self, *args, **kwargs):
        # 如果number_int为空，尝试从number中提取数字
        if not self.number_int:
            try:
                self.number_int = int(''.join(filter(str.isdigit, self.number)))
            except ValueError:
                pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Table'
        verbose_name_plural = 'Tables'
        ordering = ['number_int']

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    table_number = models.CharField(max_length=10)
    guest_count = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completion Time')
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Order #{self.id}"

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.item.name} x {self.quantity}"

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Restaurant Admin'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name='Menu Item')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantity')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.menu_item.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity
