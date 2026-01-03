from collections import deque
import threading
from typing import Optional, Tuple, List


class MatchingQueue:
    """匹配队列管理器，用于管理等待匹配的用户"""

    def __init__(self):
        self.queue = deque()  # 随机匹配队列
        self.keyword_queue = {}  # 关键词队列 {keyword: [user_ids]}
        self.user_profiles = {}  # 用户资料 {user_id: {keywords, bio, purpose}}
        self.lock = threading.Lock()

    def add(self, user_id):
        """添加用户到等待队列（随机匹配）"""
        with self.lock:
            if user_id not in self.queue:
                self.queue.append(user_id)

    def add_with_profile(self, user_id: str, profile: dict):
        """
        添加用户到关键词匹配队列

        Args:
            user_id: 用户ID
            profile: 用户资料 {'keywords': [...], 'bio': '...', 'purpose': '...'}
        """
        with self.lock:
            keywords = profile.get('keywords', [])

            # 存储用户资料
            self.user_profiles[user_id] = profile

            # 将用户ID添加到每个关键词的队列中
            for keyword in keywords:
                if keyword not in self.keyword_queue:
                    self.keyword_queue[keyword] = []

                if user_id not in self.keyword_queue[keyword]:
                    self.keyword_queue[keyword].append(user_id)

    def try_match(self, user_id):
        """
        尝试随机匹配，返回匹配的用户ID或None

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

    def try_keyword_match(self, user_id: str, profile: dict) -> Optional[Tuple[str, float]]:
        """
        尝试基于关键词匹配

        Args:
            user_id: 当前用户ID
            profile: 当前用户资料 {'keywords': [...], 'bio': '...', 'purpose': '...'}

        Returns:
            (匹配用户ID, 相似度分数) 或 None
        """
        with self.lock:
            keywords = profile.get('keywords', [])

            if not keywords:
                return None

            # 收集所有候选用户（基于关键词重合）
            candidate_users = {}

            for keyword in keywords:
                if keyword in self.keyword_queue:
                    for candidate_id in self.keyword_queue[keyword]:
                        if candidate_id != user_id:
                            if candidate_id not in candidate_users:
                                candidate_users[candidate_id] = 0
                            candidate_users[candidate_id] += 1

            if not candidate_users:
                return None

            # 找到重合关键词最多的用户
            best_match = max(candidate_users.items(), key=lambda x: x[1])
            matched_user_id = best_match[0]
            overlap_count = best_match[1]

            # 计算相似度分数
            matched_profile = self.user_profiles.get(matched_user_id, {})
            matched_keywords = matched_profile.get('keywords', [])

            # 使用 Jaccard 相似系数
            from keyword_matcher import KeywordMatcher
            similarity_score = KeywordMatcher.calculate_similarity(keywords, matched_keywords)

            # 清理匹配队列中的这两个用户
            self._remove_user_from_keyword_queue(user_id, keywords)
            self._remove_user_from_keyword_queue(matched_user_id, matched_keywords)

            return (matched_user_id, similarity_score)

    def _remove_user_from_keyword_queue(self, user_id: str, keywords: list):
        """从关键词队列中移除用户"""
        for keyword in keywords:
            if keyword in self.keyword_queue:
                if user_id in self.keyword_queue[keyword]:
                    self.keyword_queue[keyword].remove(user_id)

                # 如果该关键词队列为空，删除该键
                if not self.keyword_queue[keyword]:
                    del self.keyword_queue[keyword]

        # 清理用户资料
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]

    def remove(self, user_id):
        """从队列移除用户（断开连接时调用）"""
        with self.lock:
            # 从随机队列移除
            if user_id in self.queue:
                self.queue.remove(user_id)

            # 从关键词队列移除
            if user_id in self.user_profiles:
                keywords = self.user_profiles[user_id].get('keywords', [])
                self._remove_user_from_keyword_queue(user_id, keywords)

    def get_waiting_count(self):
        """获取当前等待人数（随机队列）"""
        with self.lock:
            return len(self.queue)
