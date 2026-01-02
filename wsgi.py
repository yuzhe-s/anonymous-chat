import os
from app import app, socketio, db

# 生产环境配置
if __name__ != '__main__':
    # 使用环境变量配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

    # 创建数据库表
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    # 开发环境
    with app.app_context():
        db.create_all()

    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
