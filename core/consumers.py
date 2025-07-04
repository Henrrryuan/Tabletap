import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Order, Table
from decimal import Decimal

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 将连接的客户端加入订单更新组
        await self.channel_layer.group_add(
            "order_updates",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # 将客户端从订单更新组中移除
        await self.channel_layer.group_discard(
            "order_updates",
            self.channel_name
        )

    async def receive(self, text_data):
        # 处理接收到的消息
        pass

    @database_sync_to_async
    def get_today_stats(self):
        today = timezone.now().date()
        today_orders = Order.objects.filter(created_at__date=today)
        return {
            'total_orders': today_orders.count(),
            'total_revenue': str(sum(order.total_amount for order in today_orders))
        }

    async def order_update(self, event):
        # 获取最新的统计数据
        stats = await self.get_today_stats()
        
        # 发送订单更新消息给客户端
        await self.send(text_data=json.dumps({
            'type': event['type'],
            'order': event['order'],
            'total_orders': stats['total_orders'],
            'total_revenue': stats['total_revenue'],
            'order_date': timezone.now().date().isoformat()
        }))

    async def new_order(self, event):
        # 获取最新的统计数据
        stats = await self.get_today_stats()
        
        # 发送新订单消息给WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'order': event['order'],
            'total_orders': stats['total_orders'],
            'total_revenue': stats['total_revenue'],
            'order_date': timezone.now().date().isoformat()
        }))

class TableConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 加入餐桌更新组
        await self.channel_layer.group_add(
            "table_updates",
            self.channel_name
        )
        await self.accept()
        
        # 发送初始餐桌数据
        tables = await self.get_tables()
        await self.send(text_data=json.dumps({
            'type': 'table_update',
            'tables': tables
        }))

    async def disconnect(self, close_code):
        # 离开餐桌更新组
        await self.channel_layer.group_discard(
            "table_updates",
            self.channel_name
        )

    async def table_update(self, event):
        # 发送餐桌更新消息给WebSocket
        await self.send(text_data=json.dumps({
            'type': 'table_update',
            'tables': event['tables']
        }))

    @database_sync_to_async
    def get_tables(self):
        # 获取所有餐桌信息
        tables = Table.objects.all().order_by('number_int')
        return [
            {
                'id': table.id,
                'number': table.number,
                'seats': table.seats,
                'is_occupied': table.is_occupied
            }
            for table in tables
        ] 