# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: main.py
@time: 2022/3/21 19:32
@description:
对于每组数据，选手的程序所有计算步骤（包含读取输入、计算、输出方案）所用时间总和不超过300秒。
若程序运行超时、运行出错或输出不合法的解（包括调度分配方案不满足题目约束或解格式不正确），
则判定无成绩。
"""
import sys
import datetime
from ReadData import read_data
# from CallSolver import construct_scheduling_model
from CallAlgorithm import algorithm
from utils import Parameter
parameter = Parameter()


def main(methd=parameter.method):
    """
    主程序
    :param methd: 求解方法，默认为使用启发式算法
    :return:
    """
    if 'win' not in sys.platform:
        print("程序开始，后续将禁用打印到控制台！")
        sys.stdout = None

    print("程序开始，当前时刻为{}！".format(datetime.datetime.now()))
    customer_list, site_list, qos, qos_constraint = read_data()
    if methd == 'solver':
        # construct_scheduling_model(customer_list, site_list, qos, qos_constraint)
        print("当前系统不支持！")
    elif methd == 'algorithm':
        algorithm(customer_list, site_list, qos, qos_constraint)
    else:
        raise Exception("求解方式错误！")


if __name__ == '__main__':
    if parameter.env is 'norm':
        main()
    else:  # 函数性能分析
        import cProfile
        import pstats
        cProfile.run("main()", filename="performance_test.txt", sort="cumulative")
        p = pstats.Stats("performance_test.txt")
        p.strip_dirs().sort_stats("cumulative", "name").print_stats(0.5)
