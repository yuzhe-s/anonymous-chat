from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta

db = SQLAlchemy()

# 北京时间（UTC+8）
def get_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))

class ChatRoom(db.Model):
    """聊天室模型"""
    __tablename__ = 'chat_rooms'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.String(100), nullable=False)
    user2_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    is_active = db.Column(db.Boolean, default=True)

    # 关联消息
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
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
