from collections import deque
import threading

class MatchingQueue:
    """匹配队列管理器，用于管理等待匹配的用户"""

    def __init__(self):
        self.queue = deque()
        self.lock = threading.Lock()

    def add(self, user_id):
        """添加用户到等待队列"""
        with self.lock:
            if user_id not in self.queue:
                self.queue.append(user_id)

    def try_match(self, user_id):
        """
        尝试匹配，返回匹配的用户ID或None

        Args:
            user_id: 当前用户ID

        Returns:
            str: 匹配到的用户ID，如果没有匹配则返回None
        """
        with self.lock:
            if len(self.queue) > 0:
                # 从队列取出第一个等待的用户
                matched_user = self.queue.popleft()

                # 确保不是自己
                if matched_user == user_id:
                    if len(self.queue) > 0:
                        # 把自己放回队列，取下一个
                        self.queue.append(matched_user)
                        matched_user = self.queue.popleft()
                    else:
                        # 队列里只有自己，放回去
                        self.queue.append(matched_user)
                        return None

                return matched_user
            return None

    def remove(self, user_id):
        """从队列移除用户（断开连接时调用）"""
        with self.lock:
            if user_id in self.queue:
                self.queue.remove(user_id)

    def get_waiting_count(self):
        """获取当前等待人数"""
        with self.lock:
            return len(self.queue)
