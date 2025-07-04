#!/bin/bash

# 设置错误处理
set -e

echo "Starting deployment process..."

# 激活虚拟环境
echo "Activating virtual environment..."
source venv/bin/activate

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 收集静态文件
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 应用数据库迁移
echo "Applying database migrations..."
python manage.py migrate

# 确保日志目录存在
mkdir -p logs

# 使用 gunicorn 启动应用
echo "Starting Gunicorn..."
gunicorn -c gunicorn_config.py tabletap.wsgi:application --log-file=logs/gunicorn.log --log-level=debug 