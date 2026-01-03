import os

class Config:
    """Flask应用配置"""

    # 安全密钥（生产环境请使用环境变量）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库配置
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///chat.db'
    # Render 的 Postgres URL 使用 postgres://，需要改为 postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 禁用连接池，兼容 eventlet
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': None,
        'pool_pre_ping': True
    }

    # Session配置
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24小时
