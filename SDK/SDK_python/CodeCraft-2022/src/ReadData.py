# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: ReadData.py
@time: 2022/3/21 16:21
@description:
"""
import csv
import datetime
import os
import numpy as np

data_path = os.path.dirname(os.getcwd()) + '/data/'
solution_path = os.path.dirname(os.getcwd()) + '/output/solution.txt'
demand_file_name = 'demand.csv'
qos_file_name = 'qos.csv'
site_bandwidth_file_name = 'site_bandwidth.csv'
config_file_name = 'config.ini'


class Customer:
    """申明客户节点类"""

    def __init__(self, name):

        self.name = name  # 客户姓名
        self.mtime = []  # 时刻列表，内部元素为时间类型（datetime类型）
        self.demand = []  # 带宽需求，内部元素为int类型

    def check_equality(self):
        """mtime和demand列表长度应相同"""
        assert len(self.mtime) == len(self.demand)


class Site:
    """申明边缘节点类"""

    def __init__(self, name, band_width):

        self.name = name  # 节点名称
        self.band_width = band_width  # 节点带宽大小


def read_data():
    """
    从data目录读取数据，并转换为内部可读取数据
    :return: cus_list: 客户类对象列表
    :return: sit_list: 边缘节点类对象列表
    :return: qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :return qos_const: 客户节点和边缘节点之间的网络质量
    """
    cus_list = []  # 客户类对象列表
    sit_list = []  # 边缘节点类对象列表
    qos_dict = {}  # 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value

    # 需求数据
    with open(data_path + demand_file_name, 'r') as f:
        results = list(csv.reader(f))
        first_line = results[0]
        for cus in first_line[1:]:
            cus_list.append(
                Customer(cus)
            )
        for demand in results[1:]:
            # mtime = int(time.mktime(time.strptime(demand[0], "%Y-%m-%dT%H:%M")))
            mtime = datetime.datetime.strptime(demand[0], "%Y-%m-%dT%H:%M")
            for i in range(len(demand[1:])):
                cus_list[i].mtime.append(mtime)
                cus_list[i].demand.append(int(demand[i + 1]))
    for cus in cus_list:
        cus.check_equality()

    # 边缘节点数据
    with open(data_path + site_bandwidth_file_name, 'r') as f:
        site_info = csv.reader(f)
        site_info.__next__()  # 跳过表头
        for site in site_info:
            site_name = site[0]
            band_width = int(site[1])
            assert band_width >= 0
            sit_list.append(
                Site(site_name, band_width)
            )

    # 网络时延数据
    qos_data = np.loadtxt(
        data_path + qos_file_name,
        dtype='float',
        delimiter=',',
        skiprows=1,
        usecols=(i for i in range(1, len(cus_list) + 1))
    )
    with open(data_path + qos_file_name, 'r') as f:
        qos_results = list(csv.reader(f))
        cus_name = qos_results[0][1:]
        for i in range(len(qos_results[1:])):
            site_name = qos_results[1:][i][0]
            for j in range(len(cus_name)):
                qos_dict[site_name, cus_name[j]] = int(qos_data[i][j])

    # 读取QoS约束上限
    with open(data_path + config_file_name, mode='r', encoding="utf-8") as f:
        lines = f.readlines()
        qos_const = int(lines[1].replace('qos_constraint=', ''))

    return cus_list, sit_list, qos_dict, qos_const


if __name__ == '__main__':
    print(read_data())
