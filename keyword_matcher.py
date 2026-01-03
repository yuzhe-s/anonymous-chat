"""
关键词提取和匹配器
用于从用户输入的目的中提取关键词，并计算用户之间的相似度
"""
import re
from collections import Counter
from typing import List, Tuple, Optional


class KeywordMatcher:
    """关键词提取和匹配器"""

    # 常用中文停用词（无实际意义的词）
    STOP_WORDS = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
        '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
        '看', '好', '自己', '这', '想', '找', '可以', '那个', '什么', '聊', '聊天',
        '想', '想找', '那个', '一些', '那个', '个', '吗', '吧', '啊', '呢', '嘛',
        '还', '就是', '都是', '或者', '但是', '然后', '因为', '所以', '如果', '虽然'
    }

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 输入文本
            max_keywords: 最大关键词数量

        Returns:
            关键词列表（按词频降序）
        """
        if not text:
            return []

        # 1. 移除特殊字符，保留中文、英文、数字
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)

        # 2. 分词（按空格和常见分隔符）
        words = re.split(r'[\s,，、.。;；:：]', text.lower())

        # 3. 过滤停用词和短词
        keywords = [
            word.strip() for word in words
            if word.strip()
            and len(word.strip()) >= 2  # 至少2个字符
            and word.strip() not in KeywordMatcher.STOP_WORDS
        ]

        if not keywords:
            return []

        # 4. 统计词频
        word_freq = Counter(keywords)

        # 5. 返回最常见的关键词
        return [word for word, _ in word_freq.most_common(max_keywords)]

    @staticmethod
    def calculate_similarity(keywords1: List[str], keywords2: List[str]) -> float:
        """
        计算两组关键词的相似度（Jaccard相似系数）

        Args:
            keywords1: 关键词列表1
            keywords2: 关键词列表2

        Returns:
            相似度分数 (0-1之间，1表示完全相同)
        """
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        # Jaccard相似系数 = 交集大小 / 并集大小
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def find_best_match(
        user_keywords: List[str],
        candidate_profiles: List[dict],
        min_similarity: float = 0.2
    ) -> Optional[Tuple[str, float]]:
        """
        从候选用户中找到最佳匹配

        Args:
            user_keywords: 当前用户的关键词
            candidate_profiles: 候选用户资料列表 [{'user_id': 'xxx', 'keywords': [...]}, ...]
            min_similarity: 最小相似度阈值

        Returns:
            (匹配用户ID, 相似度分数) 或 None
        """
        best_match = None
        best_score = 0.0

        for profile in candidate_profiles:
            candidate_keywords = profile.get('keywords', [])
            if not candidate_keywords:
                continue

            score = KeywordMatcher.calculate_similarity(user_keywords, candidate_keywords)

            if score >= min_similarity and score > best_score:
                best_score = score
                best_match = profile['user_id']

        return (best_match, best_score) if best_match else None
