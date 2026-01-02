from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
from models import db, ChatRoom, Message
from matching_queue import MatchingQueue
from config import Config
import uuid

# 初始化Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
db.init_app(app)
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

# 全局匹配队列
matching_queue = MatchingQueue()

# 在线用户追踪 {user_id: {'sid': session_id, 'room_id': room_id}}
online_users = {}


@app.route('/')
def index():
    """主页面，生成匿名用户ID"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]  # 生成8位短UUID
    return render_template('index.html', user_id=session['user_id'])


@socketio.on('connect')
def handle_connect():
    """处理WebSocket连接"""
    user_id = session.get('user_id')
    if user_id:
        print(f"用户 {user_id} 已连接")


@socketio.on('join_queue')
def handle_join_queue():
    """处理加入匹配队列"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': '无效的用户ID'})
        return

    # 检查用户是否已在房间中
    if user_id in online_users and online_users[user_id].get('room_id'):
        emit('error', {'message': '您已在聊天中'})
        return

    # 记录 SocketIO session ID
    online_users[user_id] = {'sid': request.sid, 'room_id': None}

    # 尝试匹配
    matched_user = matching_queue.try_match(user_id)

    if matched_user:
        # 创建房间
        room = ChatRoom(user1_id=user_id, user2_id=matched_user)
        db.session.add(room)
        db.session.commit()

        # 双方加入 SocketIO room
        room_id = str(room.id)
        join_room(room_id)

        # 获取对方的 session ID
        matched_sid = online_users[matched_user]['sid']
        join_room(room_id, sid=matched_sid)

        # 更新在线用户信息
        online_users[user_id]['room_id'] = room_id
        online_users[matched_user]['room_id'] = room_id

        # 通知双方匹配成功
        socketio.emit('matched', {'room_id': room_id}, room=room_id)

        print(f"匹配成功: {user_id} <-> {matched_user}, 房间ID: {room_id}")
    else:
        # 加入等待队列
        matching_queue.add(user_id)
        emit('waiting', {'message': '等待匹配中...', 'waiting_count': matching_queue.get_waiting_count()})
        print(f"用户 {user_id} 加入等待队列")


@socketio.on('send_message')
def handle_message(data):
    """处理发送消息"""
    user_id = session.get('user_id')
    content = data.get('content', '').strip()

    if not content:
        return

    # 消息长度限制
    if len(content) > 500:
        emit('error', {'message': '消息长度不能超过500字符'})
        return

    # 获取用户房间
    user_info = online_users.get(user_id)
    if not user_info or not user_info['room_id']:
        emit('error', {'message': '未在聊天中'})
        return

    room_id = user_info['room_id']

    # 保存消息到数据库
    message = Message(
        room_id=int(room_id),
        sender_id=user_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()

    # 广播到房间
    socketio.emit('new_message', {
        'sender_id': user_id,
        'content': content,
        'timestamp': message.timestamp.isoformat()
    }, room=room_id)

    print(f"用户 {user_id} 在房间 {room_id} 发送消息")


@socketio.on('leave_room_event')
def handle_leave_room():
    """处理离开房间"""
    user_id = session.get('user_id')
    user_info = online_users.get(user_id)

    if not user_info or not user_info['room_id']:
        return

    room_id = user_info['room_id']

    # 标记房间为不活跃
    room = ChatRoom.query.get(int(room_id))
    if room:
        room.is_active = False
        db.session.commit()

    # 通知对方
    socketio.emit('partner_left', {'message': '对方已离开聊天'}, room=room_id, include_self=False)

    # 自己离开 SocketIO room
    leave_room(room_id)
    online_users[user_id]['room_id'] = None

    emit('left_room', {'message': '您已离开聊天'})

    print(f"用户 {user_id} 离开房间 {room_id}")


@socketio.on('disconnect')
def handle_disconnect():
    """处理连接断开"""
    user_id = session.get('user_id')
    if not user_id:
        return

    # 从匹配队列移除
    matching_queue.remove(user_id)

    # 如果在房间中，通知对方
    if user_id in online_users:
        user_info = online_users[user_id]
        if user_info.get('room_id'):
            room_id = user_info['room_id']

            # 标记房间不活跃
            room = ChatRoom.query.get(int(room_id))
            if room:
                room.is_active = False
                db.session.commit()

            # 通知对方
            socketio.emit('partner_left', {'message': '对方已断开连接'}, room=room_id)

        # 清理在线用户记录
        del online_users[user_id]

    print(f"用户 {user_id} 已断开连接")


if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
        print("数据库表已创建")

    # 启动应用
    print("匿名聊天室启动在 http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
