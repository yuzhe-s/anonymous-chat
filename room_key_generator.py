"""
房间秘钥生成和管理器
生成唯一的房间秘钥，支持秘钥验证
"""
import random
import string
import re


class RoomKeyGenerator:
    """房间秘钥生成和管理器"""

    # 秘钥字符集（避免易混淆字符：0OI1l）
    KEY_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

    @staticmethod
    def generate_key(length: int = 8) -> str:
        """
        生成随机秘钥

        Args:
            length: 秘钥长度，默认8位

        Returns:
            随机秘钥字符串
        """
        return ''.join(random.choice(RoomKeyGenerator.KEY_CHARS) for _ in range(length))

    @staticmethod
    def generate_unique_key(existing_keys: set = None, max_attempts: int = 10) -> str:
        """
        生成唯一的秘钥（确保不与现有秘钥冲突）

        Args:
            existing_keys: 已存在的秘钥集合
            max_attempts: 最大尝试次数

        Returns:
            唯一的秘钥
        """
        if existing_keys is None:
            existing_keys = set()

        for _ in range(max_attempts):
            key = RoomKeyGenerator.generate_key()

            if key not in existing_keys:
                return key

        # 如果随机生成失败，使用更长的秘钥
        return RoomKeyGenerator.generate_key(12)

    @staticmethod
    def validate_key(key: str) -> bool:
        """
        验证秘钥格式

        Args:
            key: 待验证的秘钥

        Returns:
            是否有效
        """
        if not key or len(key) < 6 or len(key) > 12:
            return False

        # 检查是否只包含合法字符
        return all(c in RoomKeyGenerator.KEY_CHARS for c in key.upper())

    @staticmethod
    def format_key(key: str) -> str:
        """
        格式化秘钥（转大写，移除空格和特殊字符）

        Args:
            key: 原始秘钥

        Returns:
            格式化后的秘钥
        """
        if not key:
            return ''

        # 移除所有非字母数字字符，转大写
        return re.sub(r'[^A-Za-z0-9]', '', key).upper()
