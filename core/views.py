from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Menu, MenuItem, Category, Order, OrderItem, Table, CartItem
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from .decorators import admin_required, staff_required
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
import json
import os
from django.contrib.sites.models import Site
from django.urls import reverse
import qrcode
from django.conf import settings
import re
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# 主页视图
def index(request):
    response = None
    
    # 清除任何可能存在的错误消息
    if 'messages.error' in request.session:
        del request.session['messages.error']
    
    # 根据用户类型重定向
    if request.user.is_authenticated:
        if request.user.is_superuser:
            response = redirect('admin:index')  # 管理员重定向到Django Admin
        elif request.user.is_staff:
            response = redirect('staff_dashboard')  # 员工重定向到员工仪表板
        else:
            # 普通用户（顾客）不自动重定向，让他们选择是否开始点餐
            response = render(request, "core/home.html")
    else:
        # 未登录用户显示首页
        response = render(request, "core/home.html")
    
    # 添加缓存控制头
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# 登出视图
def logout_view(request):
    # 保存用户类型以确定重定向
    was_staff = request.user.is_staff
    
    # 清除所有session数据
    request.session.flush()
    
    # 执行登出
    logout(request)
    
    # 清除所有cookies
    response = redirect('index')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    
    # 添加缓存控制头
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

# 员工登录视图
def login_view(request):
    # 已登录用户的重定向逻辑
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin:index')
        elif request.user.is_staff:
            return redirect('staff_dashboard')
        else:
            return redirect('customer_login')  # 普通用户重定向到顾客登录页
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('staff_dashboard')
            else:
                messages.error(request, 'You are not a staff member and cannot login to the staff system')
        else:
            messages.error(request, 'Username or password is incorrect')
    
    return render(request, 'core/login.html')

# 顾客登录视图
def customer_login_view(request):
    # 已登录用户的重定向逻辑
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin:index')
        elif request.user.is_staff:
            return redirect('staff_dashboard')
        else:
            if request.session.get('table_number') and request.session.get('guest_count'):
                return redirect('menu_item_list')
            return redirect('menu_welcome')
    
    response = render(request, 'core/customer_login.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@staff_required
def staff_dashboard(request):
    """员工仪表板视图"""
    # 获取今日订单数量
    today = timezone.now().date()
    today_orders_count = Order.objects.filter(created_at__date=today).count()
    
    # 获取待处理订单数量
    pending_orders_count = Order.objects.exclude(status='completed').count()
    
    # 获取使用中的餐桌数量
    occupied_tables_count = Table.objects.filter(is_occupied=True).count()
    
    context = {
        'today_orders_count': today_orders_count,
        'pending_orders_count': pending_orders_count,
        'occupied_tables_count': occupied_tables_count,
    }
    
    return render(request, 'core/staff_dashboard.html', context)

@login_required
def cart_view(request):
    # 检查是否已选择桌号和人数
    if 'table_number' not in request.session or 'guest_count' not in request.session:
        # 保存当前URL到session
        request.session['return_url'] = request.get_full_path()
        return redirect('menu_welcome')
    
    # 获取当前用户的购物车
    cart_items = CartItem.objects.filter(user=request.user)
    print('!gouwuch',cart_items)
    # 计算总价和服务费
    total = sum(item.menu_item.price * item.quantity for item in cart_items)
    service_fee = total * Decimal('0.1')  # 10% 服务费
    grand_total = total + service_fee
    
    # 获取用餐信息
    table_number = request.session.get('table_number', '')
    guest_count = request.session.get('guest_count', '')
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'service_fee': service_fee,
        'grand_total': grand_total,
        'table_number': table_number,
        'guest_count': guest_count,
    }

    
    return render(request, "core/cart.html", context)

@login_required
def cart_update(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'})
        
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        cart_item.quantity = quantity
        cart_item.save()
        
        # Calculate updated cart totals
        cart_items = CartItem.objects.filter(user=request.user)
        total = sum(item.menu_item.price * item.quantity for item in cart_items)
        service_fee = total * Decimal('0.1')
        grand_total = total + service_fee
        
        return JsonResponse({
            'success': True,
            'total': str(total),
            'service_fee': str(service_fee),
            'grand_total': str(grand_total)
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cart item does not exist'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid quantity'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def cart_remove(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        cart_item.delete()
        
        return JsonResponse({'success': True})
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cart item does not exist'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def cart_checkout(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # 获取购物车商品
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        # 获取用餐信息
        table_number = request.session.get('table_number')
        guest_count = request.session.get('guest_count')
        
        if not table_number or not guest_count:
            return JsonResponse({'success': False, 'error': 'Please select table number and guest count first'})
        
        # 计算总价和服务费
        total = sum(item.menu_item.price * item.quantity for item in cart_items)
        service_fee = total * Decimal('0.1')  # 10% 服务费
        grand_total = total + service_fee
        
        # 生成订单号 (年月日时分秒+4位随机数)
        from datetime import datetime
        import random
        order_number = datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(1000, 9999))
        
        # 创建订单
        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            table_number=table_number,
            guest_count=guest_count,
            total_amount=total,
            service_fee=service_fee,
            grand_total=grand_total,
            status='pending'
        )
        
        # 创建订单项
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                item=cart_item.menu_item,
                quantity=cart_item.quantity,
                price_at_time=cart_item.menu_item.price
            )
        
        # 清空购物车
        cart_items.delete()
        
        # 更新餐桌状态
        table = Table.objects.get(number=table_number)
        table.is_occupied = True
        table.last_order_time = timezone.now()
        table.save()
        
        return JsonResponse({
            'success': True,
            'order_number': order_number,
            'redirect_url': reverse('order_success', args=[order_number])
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def order_success(request, order_number):
    # 获取订单
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'core/order_success.html', {'order': order})

@staff_required #处理订单日期和分页
def order_list(request):
    """订单列表视图"""
    # 获取日期过滤参数
    filter_date = request.GET.get('date')
    if filter_date:
        try:
            filter_date = timezone.datetime.strptime(filter_date, '%Y-%m-%d').date()
        except ValueError:
            filter_date = timezone.now().date()
    else:
        filter_date = timezone.now().date()
    
    # 获取状态过滤参数
    status_filter = request.GET.get('status', '')
    
    # 获取所有订单并按日期过滤
    orders = Order.objects.filter(created_at__date=filter_date)
    
    # 应用状态过滤
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # 计算选中日期的订单统计（只统计已完成的订单）
    completed_orders = orders.filter(status='completed')
    total_orders = completed_orders.count()
    total_revenue = sum(order.grand_total for order in completed_orders)
    
    # 按创建时间倒序排序
    orders = orders.order_by('-created_at')
    
    # 分页处理
    paginator = Paginator(orders, 6)  # 每页显示6个订单
    page = request.GET.get('page')
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'filter_date': filter_date,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    # 如果是AJAX请求，只返回统计数据
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'total_orders': total_orders,
            'total_revenue': float(total_revenue)
        })
    
    return render(request, 'core/order_list.html', context)

@staff_required
@require_POST
def mark_order_completed(request, order_id):
    """标记订单为已完成"""
    try:
        order = get_object_or_404(Order, id=order_id)
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        
        # 返回更新后的统计数据
        today = timezone.now().date()
        completed_orders = Order.objects.filter(
            created_at__date=today,
            status='completed'
        )
        total_orders = completed_orders.count()
        total_revenue = sum(order.grand_total for order in completed_orders)
        
        return JsonResponse({
            'success': True,
            'total_orders': total_orders,
            'total_revenue': float(total_revenue)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@admin_required
def menu_list(request):
    """员工菜品管理视图"""
    # 获取所有菜品
    menu_items = MenuItem.objects.all().order_by('category', 'name')
    
    # 获取所有分类
    categories = Category.objects.all().order_by('name')
    
    # 获取搜索参数
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '')
    
    # 应用搜索过滤
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 应用分类过滤
    if category_id:
        menu_items = menu_items.filter(category_id=category_id)
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id
    }
    
    return render(request, 'core/menu_item_list.html', context)

@admin_required #添加新菜品
def menu_item_create(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            image = request.FILES.get('image')
            
            if not name or not price:
                return redirect('menu_item_create')
            
            # 获取或创建默认活动菜单
            active_menu = Menu.objects.filter(is_active=True).first()
            if not active_menu:
                active_menu = Menu.objects.create(
                    name='Default Menu',
                    description='Automatically created default menu',
                    is_active=True
                )
            
            # 创建新菜品
            item = MenuItem.objects.create(
                name=name,
                description=description,
                price=price,
                category_id=category_id,
                menu=active_menu,  # 关联到活动菜单
                is_available=True
            )
            
            if image:
                item.image = image
                item.save()
            
            # 如果是从某个分类页面添加的，返回到该分类页面
            if category_id:
                return redirect(f"{reverse('menu_item_list')}?category={category_id}")
            return redirect('menu_item_list')
            
        except Exception as e:
            return redirect('menu_item_create')
    
    # 获取当前选中的分类
    category_id = request.GET.get('category')
    category = None
    if category_id:
        category = get_object_or_404(Category, id=category_id)
    
    categories = Category.objects.all()
    return render(request, 'core/menu_item_form.html', {
        'categories': categories,
        'selected_category': category
    })

@admin_required #编辑菜品
def menu_item_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        try:
            item.name = request.POST.get('name')
            item.description = request.POST.get('description')
            item.price = request.POST.get('price')
            category_id = request.POST.get('category')
            item.category = get_object_or_404(Category, pk=category_id)
            item.is_available = request.POST.get('is_available') == 'on'
            
            # 处理图片上传
            image = request.FILES.get('image')
            if image:
                # 如果已经有图片，先删除旧图片
                if item.image:
                    old_image_path = item.image.path
                    if os.path.isfile(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except Exception as e:
                            print(f"Error deleting old image for {item.name}: {str(e)}")
                item.image = image
            
            # 处理删除图片的情况
            delete_image = request.POST.get('delete_image') == 'true'
            if delete_image and item.image:
                old_image_path = item.image.path
                if os.path.isfile(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting image for {item.name}: {str(e)}")
                item.image = None
                
            item.save()
            
        except Exception as e:
            return redirect('menu_item_list')
        
        return redirect('menu_item_list')
    
    categories = Category.objects.all()
    return render(request, 'core/menu_item_form.html', {
        'item': item,
        'categories': categories,
        'selected_category': item.category
    })

@staff_required
def table_list(request):
    tables = Table.objects.all().order_by('number_int')
   
    for table in tables:
        table.generate_qr_code()
        table.save()
    return render(request, 'core/table_list.html', {'tables': tables})

@staff_required
def table_create(request):
    if request.method == 'POST':
        try:
            number = request.POST.get('number')
            seats = int(request.POST.get('seats'))
            
            if seats < 1:
                return redirect('table_list')
                
            if Table.objects.filter(number=number).exists():
                return redirect('table_list')
                
            table = Table.objects.create(
                number=number,
                seats=seats
            )
            
            # 生成二维码
            table.generate_qr_code()
            
        except ValueError:
            pass
        except Exception as e:
            pass
            
    return redirect('table_list')

@staff_required
def table_edit(request, pk):
    table = get_object_or_404(Table, pk=pk)
    
    if request.method == 'POST':
        try:
            number = request.POST.get('number')
            seats = int(request.POST.get('seats'))
            
            if seats < 1:
                return redirect('table_list')
            
            # 检查桌号是否已存在（排除当前桌子）
            if Table.objects.filter(number=number).exclude(pk=pk).exists():
                return redirect('table_list')
            
            table.number = number
            table.seats = seats
            table.save()
            
        except ValueError:
            pass
        except Exception as e:
            pass
    
    return redirect('table_list')

@staff_required
def table_delete(request, pk):
    if request.method == 'POST':
        table = get_object_or_404(Table, pk=pk)
        try:
            table.delete()
            return redirect('table_list')
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def table_status(request):
    """显示所有桌子的状态和二维码"""
    tables = Table.objects.all().order_by('number_int')
    context = {
        'tables': tables,
    }
    return render(request, 'core/table_status.html', context)

def table_menu(request, table_number):
    try:
        table = Table.objects.get(number=table_number)
        
        # 如果桌子已被占用且不是当前会话
        if table.is_occupied and request.session.get('table_number') != table_number:
            return redirect('index')
        
        # 如果还没有设置人数，重定向到人数选择页面
        if 'guest_count' not in request.session:
            return render(request, 'core/scan_guest_count.html', {'table_number': table_number})
        
        # 更新桌子状态
        if not table.is_occupied:
            table.is_occupied = True
            table.save()
        
        # 设置会话数据
        request.session['table_number'] = table_number
        
        # 重定向到菜单页面
        return redirect('menu_item_list')
        
    except Table.DoesNotExist:
        return redirect('index')
    
def table_selection(request):
    # 如果用户已经选择了桌号和人数，直接重定向到菜单
    if request.user.is_authenticated and request.session.get('table_number') and request.session.get('guest_count'):
        return redirect('menu_item_list')
    
    # 获取所有未被占用的餐桌
    available_tables = Table.objects.filter(is_occupied=False).order_by('number_int')
    
    context = {
        'tables': available_tables,
    }
    
    return render(request, 'core/table_selection.html', context)


    try:
        table = Table.objects.get(number=table_number)
        
        # 如果桌子已被占用且不是当前会话
        if table.is_occupied and request.session.get('table_number') != table_number:
            return redirect('index')
        
        # 如果还没有设置人数，重定向到人数选择页面
        if 'guest_count' not in request.session:
            return render(request, 'core/scan_guest_count.html', {'table_number': table_number})
        
        # 更新桌子状态
        if not table.is_occupied:
            table.is_occupied = True
            table.save()
        
        # 设置会话数据
        request.session['table_number'] = table_number
        
        # 重定向到菜单页面
        return redirect('menu_item_list')
        
    except Table.DoesNotExist:
        return redirect('index')

@require_http_methods(["POST"])
def set_guest_count(request, table_number):
    """设置用餐人数"""
    try:
        guest_count = int(request.POST.get('guest_count', 0))
        if guest_count <= 0:
            raise ValueError('Invalid guest count')
            
        table = Table.objects.get(number=table_number)
        
        # 更新会话数据
        request.session['guest_count'] = guest_count
        request.session['table_number'] = table_number
        
        # 更新桌子状态
        table.is_occupied = True
        table.save()
        
        return redirect('menu_item_list')
        
    except (ValueError, Table.DoesNotExist):
        return redirect('index')

@require_POST
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Please log in first'})
    
    try:
        data = json.loads(request.body)
        item_id = data.get('menu_item_id')
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'})
        
        # 获取菜品
        menu_item = get_object_or_404(MenuItem, id=item_id, is_available=True)
        
        # 检查购物车中是否已存在该菜品
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            menu_item=menu_item,
            defaults={'quantity': quantity}
        )
        
        # 如果购物车中已存在该菜品，更新数量
        if not created:
            cart_item.quantity += quantity  # Add to existing quantity instead of replacing
            cart_item.save()
        
        # Calculate total items in cart
        total_items = CartItem.objects.filter(user=request.user).aggregate(
            total_items=models.Sum('quantity'))['total_items'] or 0
        
        return JsonResponse({
            'success': True,
            'total_items': total_items
        })
    except MenuItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Menu item does not exist or is out of stock'})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid quantity: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to add: {str(e)}'})

@staff_required
def toggle_table_status(request, pk):
    if request.method == 'POST':
        table = get_object_or_404(Table, pk=pk)
        try:
            # 切换状态
            table.is_occupied = not table.is_occupied
            table.save()
            
            # 如果桌子被设置为空闲，清除相关的会话数据
            if not table.is_occupied:
                from django.contrib.sessions.models import Session
                from django.utils import timezone
                sessions = Session.objects.filter(expire_date__gte=timezone.now())
                
                for session in sessions:
                    session_data = session.get_decoded()
                    if session_data.get('table_number') == table.number:
                        session.delete()
            
            return JsonResponse({
                'success': True,
                'is_occupied': table.is_occupied
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_required
def category_list(request):
    """类别列表视图"""
    categories = Category.objects.all().order_by('name')
    return render(request, 'core/category_list.html', {
        'categories': categories,
    })

@staff_required
@require_POST
def category_create(request):
    """创建类别"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
        
    try:
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Category name cannot be empty'})
        
        # 检查类别名称是否已存在
        if Category.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': 'Category name already exists'})
        
        category = Category.objects.create(
            name=name,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@staff_required
@require_POST
def category_delete(request, category_id):
    """删除分类视图"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
        
    try:
        category = get_object_or_404(Category, id=category_id)
        category_name = category.name
        
        # 删除该类别下的所有菜品
        MenuItem.objects.filter(category=category).delete()
        # 删除类别
        category.delete()
        
        # 如果当前URL包含被删除的分类ID，返回重定向信息
        current_category = request.GET.get('category')
        if current_category and int(current_category) == category_id:
            return JsonResponse({
                'success': True,
                'redirect': True,
                'redirect_url': reverse('menu_item_list')
            })
        
        return JsonResponse({
            'success': True
        })
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category does not exist'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def menu_welcome(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        guest_count = request.POST.get('guest_count')
        
        if not table_number or not guest_count:
            return redirect('menu_welcome')
        
        try:
            # 获取对应的餐桌
            table = Table.objects.get(number=table_number)
            
            # 检查餐桌是否已被占用
            if table.is_occupied:
                return redirect('menu_welcome')
            
            # 更新餐桌状态为占用
            table.is_occupied = True
            table.last_order_time = timezone.now()
            table.save()
            
            # 保存信息到session
            request.session['table_number'] = table_number
            request.session['guest_count'] = int(guest_count)
            request.session.modified = True
            
            # 获取返回URL，如果没有则默认到菜单页
            return_url = request.session.pop('return_url', reverse('menu_item_list'))
            return redirect(return_url)
            
        except Table.DoesNotExist:
            return redirect('menu_welcome')
        except ValueError:
            return redirect('menu_welcome')
        except Exception:
            return redirect('menu_welcome')
    
    # GET请求处理
    available_tables = Table.objects.filter(is_occupied=False).order_by('number_int', 'number')
    
    # 更新所有餐桌的number_int
    for table in available_tables:
        if not table.number_int:
            try:
                table.number_int = int(''.join(filter(str.isdigit, table.number)))
                table.save()
            except ValueError:
                pass
    
    # 重新查询排序后的餐桌
    available_tables = Table.objects.filter(is_occupied=False).order_by('number_int', 'number')
    
    context = {
        'tables': available_tables,
        'return_url': request.session.get('return_url')
    }
    response = render(request, 'core/menu_welcome.html', context)
    # 添加缓存控制头
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def menu_item_list(request):
    """菜单列表视图"""
    # 获取所有分类
    categories = Category.objects.all().order_by('name')
    
    # 获取搜索参数
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '')
    
    # 检查是否是员工
    is_staff = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    
    # 获取菜品（对于员工显示所有菜品，对于顾客只显示可用的菜品）
    menu_items = MenuItem.objects.all()
    if not is_staff:
        menu_items = menu_items.filter(is_available=True)
        # 检查是否已选择餐桌（仅针对顾客）
        if not request.session.get('table_number') or not request.session.get('guest_count'):
            messages.info(request, 'Please select table and guest count first')
            return redirect('menu_welcome')
    
    # 应用搜索过滤
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 应用分类过滤
    if category_id:
        menu_items = menu_items.filter(category_id=category_id)
    
    # 按分类和名称排序
    menu_items = menu_items.order_by('category', 'name')
    
    # 获取当前用户的购物车项（仅针对顾客）
    cart_items = CartItem.objects.filter(user=request.user) if request.user.is_authenticated and not is_staff else []
    cart_quantities = {item.menu_item.id: item.quantity for item in cart_items}
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'cart_quantities': cart_quantities,
        'is_staff': is_staff,
        'table_number': request.session.get('table_number'),
        'guest_count': request.session.get('guest_count')
    }
    print(context)
    
    response = render(request, 'core/menu_item_list.html', context)
    # 添加缓存控制头
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@staff_required
def table_batch_create(request):
    """批量生成餐桌和对应的二维码"""
    if request.method == 'POST':
        start_number = request.POST.get('start_number')
        table_count = int(request.POST.get('table_count', 0))
        seats_per_table = int(request.POST.get('seats_per_table', 4))
        
        if not start_number or table_count <= 0 or seats_per_table <= 0:
            return redirect('table_batch_create')
        
        # 检查数量限制
        if table_count > 100:
            return redirect('table_batch_create')
        
        # 生成桌号序列
        if start_number.isdigit():
            # 纯数字桌号
            start_num = int(start_number)
            table_numbers = [str(start_num + i) for i in range(table_count)]
        else:
            # 字母+数字桌号 (例如: A01)
            prefix = ''.join(filter(str.isalpha, start_number))
            num_part = ''.join(filter(str.isdigit, start_number))
            if not num_part:
                num_part = '1'
            num_width = len(num_part)
            start_num = int(num_part)
            table_numbers = [
                f"{prefix}{str(start_num + i).zfill(num_width)}" 
                for i in range(table_count)
            ]
        
        # 检查桌号是否已存在
        existing_numbers = set(Table.objects.values_list('number', flat=True))
        conflicting_numbers = [num for num in table_numbers if num in existing_numbers]
        if conflicting_numbers:
            return redirect('table_batch_create')
        
        # 批量创建餐桌
        created_tables = []
        for table_number in table_numbers:
            table = Table.objects.create(
                number=table_number,
                seats=seats_per_table
            )
            # 生成二维码
            table.generate_qr_code()
            created_tables.append(table)
        
        return redirect('table_list')
    
    return render(request, 'core/table_batch_create.html')

@staff_required
def generate_table_qr(request, pk):
    """生成餐桌二维码的API端点"""
    if request.method == 'POST':
        try:
            table = get_object_or_404(Table, pk=pk)
            table.generate_qr_code()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@staff_required
@require_POST
def menu_item_delete(request, pk):
    """删除菜品视图"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
        
    try:
        menu_item = get_object_or_404(MenuItem, pk=pk)
        menu_item.delete()
        return JsonResponse({'success': True, 'message': 'Menu item has been successfully deleted'})
    except MenuItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Menu item does not exist'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

