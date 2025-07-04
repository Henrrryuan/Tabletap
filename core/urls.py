from django.urls import path
from django.shortcuts import redirect
from . import views

def menu_redirect(request):
    return redirect('menu_item_list')

urlpatterns = [
    # 基础路由
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('customer-login/', views.customer_login_view, name='customer_login'),
    path('logout/', views.logout_view, name='logout'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('menu-welcome/', views.menu_welcome, name='menu_welcome'),  # 添加欢迎页面路由
    
    # 菜品管理（员工入口）
    path('menu-items/create/', views.menu_item_create, name='menu_item_create'),
    path('menu-items/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu-items/<int:pk>/delete/', views.menu_item_delete, name='menu_item_delete'),
    
    # 顾客点餐入口
    path('menu-items/', views.menu_item_list, name='menu_item_list'),  # 顾客点餐入口
    path('table/<str:table_number>/menu/', views.table_menu, name='table_menu'),
    path('table/<str:table_number>/set-guest-count/', views.set_guest_count, name='set_guest_count'),
    
    # 类别管理
    path('api/categories/', views.category_list, name='category_list'),
    path('api/categories/create/', views.category_create, name='category_create'),
    path('api/categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    
    # 订单管理
    path('orders/', views.order_list, name='orders'),
    path('orders/<str:order_number>/success/', views.order_success, name='order_success'),
    path('orders/<int:order_id>/complete/', views.mark_order_completed, name='mark_order_completed'),
    # 餐桌管理
    path('tables/', views.table_list, name='table_list'),
    path('tables/create/', views.table_create, name='table_create'),
    path('tables/batch-create/', views.table_batch_create, name='table_batch_create'),
    path('tables/<int:pk>/edit/', views.table_edit, name='table_edit'),
    path('tables/<int:pk>/delete/', views.table_delete, name='table_delete'),
    path('api/tables/<int:pk>/toggle-status/', views.toggle_table_status, name='toggle_table_status'),
    path('tables/<int:pk>/generate-qr/', views.generate_table_qr, name='generate_table_qr'),
    
    # 购物车
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
]
