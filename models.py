from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
import json

db = SQLAlchemy()

# 北京时间（UTC+8）
def get_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))


class UserProfile(db.Model):
    """用户简介模型"""
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    bio = db.Column(db.Text, nullable=True)  # 用户简介
    purpose = db.Column(db.Text, nullable=True)  # 聊天目的
    keywords = db.Column(db.Text, nullable=True)  # JSON格式的关键词列表
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bio': self.bio,
            'purpose': self.purpose,
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ChatRoom(db.Model):
    """聊天室模型"""
    __tablename__ = 'chat_rooms'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.String(100), nullable=False)
    user2_id = db.Column(db.String(100), nullable=True)  # 改为可空（私密房间初始状态）
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    is_active = db.Column(db.Boolean, default=True)

    # 新增字段
    room_key = db.Column(db.String(20), unique=True, nullable=True, index=True)  # 秘钥
    match_type = db.Column(db.String(20), default='random')  # 'random', 'keyword', 'private'
    is_private = db.Column(db.Boolean, default=False)  # 是否为私密房间

    # 关联消息
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'room_key': self.room_key,
            'match_type': self.match_type,
            'is_private': self.is_private
        }


class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_id = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_beijing_time)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'sender_id': self.sender_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }
