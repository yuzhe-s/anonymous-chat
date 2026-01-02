#!/bin/bash
# Render 启动脚本

# 创建数据库表
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"

# 启动应用
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
