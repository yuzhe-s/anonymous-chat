from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
from models import db, ChatRoom, Message, UserProfile
from matching_queue import MatchingQueue
from config import Config
from keyword_matcher import KeywordMatcher
from room_key_generator import RoomKeyGenerator
import uuid
import os
import json

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


@app.route('/admin')
def admin():
    """管理后台页面 - 简单密码保护"""
    # 简单的密码验证（生产环境应该用更安全的方式）
    password = request.args.get('password')
    if password != os.environ.get('ADMIN_PASSWORD', 'admin123'):
        return "未授权访问", 401

    # 获取统计数据
    total_rooms = ChatRoom.query.count()
    total_messages = Message.query.count()
    active_rooms = ChatRoom.query.filter_by(is_active=True).count()

    stats = {
        'total_rooms': total_rooms,
        'total_messages': total_messages,
        'active_rooms': active_rooms
    }

    # 获取所有聊天室（按创建时间倒序）
    rooms = ChatRoom.query.order_by(ChatRoom.created_at.desc()).all()

    # 准备 JSON 数据用于导出
    data_json = [room.to_dict() for room in rooms]
    for room_data, room in zip(data_json, rooms):
        room_data['messages'] = [msg.to_dict() for msg in room.messages]

    return render_template('admin.html', stats=stats, rooms=rooms, data_json=data_json)


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


@socketio.on('join_queue_with_profile')
def handle_join_queue_with_profile(data):
    """带简介加入匹配队列（支持关键词匹配）"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': '无效的用户ID'})
        return

    # 检查用户是否已在房间中
    if user_id in online_users and online_users[user_id].get('room_id'):
        emit('error', {'message': '您已在聊天中'})
        return

    # 获取用户资料
    bio = data.get('bio', '').strip()
    purpose = data.get('purpose', '').strip()
    keywords_text = data.get('keywords', '').strip()

    # 提取关键词
    keywords = KeywordMatcher.extract_keywords(purpose + ' ' + keywords_text)

    # 构建资料
    profile = {
        'bio': bio,
        'purpose': purpose,
        'keywords': keywords
    }

    # 记录 SocketIO session ID
    online_users[user_id] = {'sid': request.sid, 'room_id': None}

    # 如果有关键词，先添加到关键词队列，然后尝试匹配
    if keywords:
        # 先将自己加入队列
        matching_queue.add_with_profile(user_id, profile)

        # 尝试匹配
        match_result = matching_queue.try_keyword_match(user_id, profile)

        if match_result:
            matched_user, score = match_result

            # 保存用户简介
            user_profile = UserProfile(
                user_id=user_id,
                bio=bio,
                purpose=purpose,
                keywords=json.dumps(keywords, ensure_ascii=False)
            )
            db.session.add(user_profile)

            # 保存匹配用户的简介
            matched_profile = matching_queue.user_profiles.get(matched_user, {})
            matched_user_profile = UserProfile(
                user_id=matched_user,
                bio=matched_profile.get('bio', ''),
                purpose=matched_profile.get('purpose', ''),
                keywords=json.dumps(matched_profile.get('keywords', []), ensure_ascii=False)
            )
            db.session.add(matched_user_profile)

            # 创建房间
            room = ChatRoom(
                user1_id=user_id,
                user2_id=matched_user,
                match_type='keyword'
            )
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
            socketio.emit('matched_with_score', {
                'room_id': room_id,
                'match_score': score,
                'keywords_matched': list(set(keywords) & set(matched_profile.get('keywords', [])))
            }, room=room_id)

            print(f"关键词匹配成功: {user_id} <-> {matched_user}, 分数: {score:.2f}")
            return

        # 已添加到关键词队列但暂时没有匹配，发送等待状态
        emit('waiting', {'message': '正在寻找相似话题的聊天对象...', 'waiting_count': matching_queue.get_waiting_count()})
        print(f"用户 {user_id} 加入关键词匹配队列")

    # 如果没有关键词，加入随机队列
    else:
        matching_queue.add(user_id)
        emit('waiting', {'message': '等待匹配中...', 'waiting_count': matching_queue.get_waiting_count()})
        print(f"用户 {user_id} 加入随机等待队列")


@socketio.on('create_private_room')
def handle_create_private_room(data):
    """创建私密房间"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': '无效的用户ID'})
        return

    # 检查用户是否已在房间中
    if user_id in online_users and online_users[user_id].get('room_id'):
        emit('error', {'message': '您已在聊天中'})
        return

    # 生成唯一秘钥
    existing_keys = set(r.room_key for r in ChatRoom.query.filter(ChatRoom.room_key.isnot(None)).all())
    room_key = RoomKeyGenerator.generate_unique_key(existing_keys)

    # 获取用户资料
    bio = data.get('bio', '').strip()
    purpose = data.get('purpose', '').strip()
    keywords_text = data.get('keywords', '').strip()
    keywords = KeywordMatcher.extract_keywords(purpose + ' ' + keywords_text)

    # 创建房间
    room = ChatRoom(
        user1_id=user_id,
        user2_id=None,  # 私密房间初始为空
        room_key=room_key,
        match_type='private',
        is_private=True
    )
    db.session.add(room)

    # 保存用户简介
    user_profile = UserProfile(
        user_id=user_id,
        bio=bio,
        purpose=purpose,
        keywords=json.dumps(keywords, ensure_ascii=False)
    )
    db.session.add(user_profile)
    db.session.commit()

    # 加入 SocketIO room
    room_id = str(room.id)
    join_room(room_id)

    online_users[user_id] = {'sid': request.sid, 'room_id': room_id}

    emit('private_room_created', {
        'room_key': room_key,
        'room_id': room_id,
        'message': f'私密房间已创建！\n\n🔑 秘钥：{room_key}\n\n分享给朋友，让他们输入此秘钥加入房间。'
    })

    print(f"用户 {user_id} 创建私密房间，秘钥：{room_key}")


@socketio.on('join_private_room')
def handle_join_private_room(data):
    """通过秘钥加入私密房间"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': '无效的用户ID'})
        return

    room_key = data.get('room_key', '').strip().upper()

    # 验证秘钥格式
    if not RoomKeyGenerator.validate_key(room_key):
        emit('error', {'message': '无效的秘钥格式'})
        return

    # 查找房间
    room = ChatRoom.query.filter_by(room_key=room_key, is_private=True).first()
    if not room:
        emit('error', {'message': '秘钥不存在'})
        return

    # 检查房间是否已满
    if room.user2_id and room.user2_id != user_id:
        emit('error', {'message': '房间已满'})
        return

    # 获取用户资料
    bio = data.get('bio', '').strip()
    purpose = data.get('purpose', '').strip()
    keywords_text = data.get('keywords', '').strip()
    keywords = KeywordMatcher.extract_keywords(purpose + ' ' + keywords_text)

    # 记录 SocketIO session ID
    online_users[user_id] = {'sid': request.sid, 'room_id': str(room.id)}

    # 加入房间
    room_id = str(room.id)
    join_room(room_id)

    # 更新房间信息
    if not room.user2_id:
        room.user2_id = user_id
        room.is_active = True

    # 保存用户简介
    user_profile = UserProfile(
        user_id=user_id,
        bio=bio,
        purpose=purpose,
        keywords=json.dumps(keywords, ensure_ascii=False)
    )
    db.session.add(user_profile)
    db.session.commit()

    # 加载历史消息
    messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.asc()).all()
    history = [msg.to_dict() for msg in messages]

    # 通知双方
    socketio.emit('joined_private_room', {
        'room_id': room_id,
        'room_key': room_key,
        'has_history': len(history) > 0,
        'message': '已加入私密房间'
    }, room=room_id)

    # 如果有历史记录，发送给新加入的用户
    if history:
        emit('room_history', {'messages': history})

    print(f"用户 {user_id} 通过秘钥加入房间 {room_key}")


@socketio.on('get_room_history')
def handle_get_room_history(data):
    """获取房间历史记录（通过秘钥查看）"""
    room_key = data.get('room_key', '').strip().upper()

    # 验证秘钥
    room = ChatRoom.query.filter_by(room_key=room_key).first()
    if not room:
        emit('error', {'message': '秘钥不存在'})
        return

    # 获取历史消息
    messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.asc()).all()
    history = [msg.to_dict() for msg in messages]

    emit('room_history', {
        'room_id': room.id,
        'room_key': room_key,
        'messages': history,
        'message_count': len(history)
    })


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
