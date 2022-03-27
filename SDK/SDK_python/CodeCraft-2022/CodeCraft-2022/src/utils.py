# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: utils.py
@time: 2022/3/24 11:17
@description:
"""
import os
import sys
from functools import wraps
import time
import heapq


class Parameter(object):
    """
    基于单例模式实现算法参数类
    """
    instance = None  # 类属性，记录第一个被创建对象的引用

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:  # 判断类属性是否为空对象
            cls.instance = super().__new__(cls)  # 调用父类方法，为第一个对象分配空间
        return cls.instance  # 返回类属性保存的对象引用

    def __init__(self):

        self.alpha = 0.5  # 初始解生成算法中用来更新下一时刻边缘节点被选择的概率

        self.data_path = '/data/'  # 读取数据的路径（默认为比赛正式环境）
        self.solution_path = '/output/solution.txt'  # 写入解决方案的路径（默认为比赛正式环境）

        self.decimal = 4  # 在算法过程中，涉及小数的保留位数，以降低时间开销

        self.env = 'norm'  # 'norm'表明当前为比赛环境，将减少部分计算以减少时间开销
        # self.env = 'test'  # 'test'表明当前为测试环境，部分功能将被使用

        self.method = 'algorithm'  # 使用何种求解方式，当前表示使用启发式算法
        # self.method = 'solver'  # 使用何种求解方式，当前表示使用Gurobi求解器

        self.degree_of_destruction = 0.25  # ALNS算法，解被破坏的比例
        self.iterations = 2000  # ALNS算法，迭代次数

    def produce_path(self):

        if 'win' in sys.platform:  # 若为本地环境，则修改为本地Windows的路径
            # test_data = 'official100t30cus100site'
            # test_data = 'simulated1000t30cus100site0.3pressure'
            # test_data = 'simulated1000t30cus100site0.99pressure'
            test_data = 'simulated500t20cus100site0.3pressure'
            # test_data = 'simulated100t10cus100site0.3pressure'
            self.data_path = os.path.join(os.path.dirname(os.getcwd()),
                                          'data',
                                          test_data)
            self.solution_path = os.path.join(os.path.dirname(os.getcwd()), 'output', 'solution.txt')


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
        print('\n函数{}.{}运行时间 : {} 秒（来自装饰器）'.format(func.__module__, func.__name__, end - start))
        return r
    return wrapper
