# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: CallAlgorithm.py
@time: 2022/3/22 20:54
@description:
"""
import math
from ReadData import read_data, solution_path


def initial_solution_generation(cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):
    """
    基于贪婪启发式算法构建流量分配模型初始解
    :param cus_list: 客户类对象列表
    :param sit_list: 边缘节点类对象列表
    :param qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :param qos_constraint: 客户节点和边缘节点之间的网络质量
    :return:
    """

    return


def algorithm(cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):
    """
    基于ALNS启发式算法对流量分配模型进行求解
    :param cus_list: 客户类对象列表
    :param sit_list: 边缘节点类对象列表
    :param qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :param qos_constraint: 客户节点和边缘节点之间的网络质量
    :return:
    """

    return


if __name__ == '__main__':
    customer_list, site_list, qos, qos_cons = read_data()
    algorithm(customer_list, site_list, qos, qos_cons)
