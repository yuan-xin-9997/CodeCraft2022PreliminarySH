# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: utils.py
@time: 2022/3/24 11:17
@description:
"""
from functools import wraps
import time
import heapq


class PriorityQueue:
    """基于Python堆队列算法库heapq实现优先级队列"""

    def __init__(self):
        self.elements = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, item, priority):
        """将 item 的值加入 heap 中，保持堆的不变性（根据priority）"""
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        """弹出并返回 heap 的最小的元素（即priority最小对应的item），保持堆的不变性"""
        return heapq.heappop(self.elements)[1]


def time_this(func):
    """统计函数func的运行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        r = func(*args, **kwargs)
        end = time.perf_counter()
        print('函数{}.{}运行时间 : {} 秒（来自装饰器）'.format(func.__module__, func.__name__, end - start))
        return r
    return wrapper
