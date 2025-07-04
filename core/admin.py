from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Category, Menu, MenuItem, Order, OrderItem, UserProfile, Table, CartItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'created_at', 'updated_at')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu', 'category', 'price', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'menu__name', 'category__name')
    list_filter = ('is_available', 'menu', 'category', 'created_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'table_number', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'table_number']
    readonly_fields = ['created_at', 'completed_at']
    inlines = [OrderItemInline]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'completed':
            return self.readonly_fields + ['status']
        return self.readonly_fields

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'seats', 'is_occupied')
    list_filter = ('is_occupied',)
    search_fields = ('number',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'price_at_time')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'item__name')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'quantity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'menu_item__name')
