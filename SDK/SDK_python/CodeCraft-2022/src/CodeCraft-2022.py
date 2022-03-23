# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: main.py
@time: 2022/3/21 19:32
@description:
"""
from ReadData import read_data
from CallSolver import construct_scheduling_model
from CallAlgorithm import algorithm
# method = 'solver'
method = 'algorithm'


def main(methd: str):
    """
    主程序
    :param methd: 求解方法
    :return:
    """
    customer_list, site_list, qos, qos_constraint = read_data()
    if methd == 'solver':
        construct_scheduling_model(customer_list, site_list, qos, qos_constraint)
    elif methd == 'algorithm':
        algorithm(customer_list, site_list, qos, qos_constraint)
    else:
        raise Exception("求解方式错误！")


if __name__ == '__main__':
    main(method)
