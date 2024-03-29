# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: Results.py
@time: 2022/3/23 21:02
@description:
"""
import math
import sys
import numpy as np
from utils import Parameter

# sys.stdout = None
parameter = Parameter()


class Results:
    """
    流量分配方案的解决方案类（TODO：是否应该设置为单例？）
    """

    def __init__(self, cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):

        # numpy三维数组，对应于变量x_ijt及其值，维度：t*i*j，及时刻数量*客户节点数量*边缘节点数量
        self.solution = np.zeros((len(cus_list[0].mtime), len(cus_list), len(sit_list)), dtype=np.int)

        self.cus_list = cus_list  # 客户类对象列表
        self.sit_list = sit_list  # 边缘节点类对象列表
        self.qos_constraint = qos_constraint  # 客户节点和边缘节点之间的网络质量阈值（超过该值将不得分配）

        self.qos_dict = qos_dict  # 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value（Python字典结构）
        self.qos_np = self.convert_qos_constraint()  # 客户节点和边缘节点之间的网络质量（Numpy二维数组结构），i*j

        self.obj_value = sys.maxsize  # 当前solution的目标函数值

        self.mtime_list = cus_list[0].mtime  # 所有客户节点共用时刻列表
        self.percentile_95 = min([math.ceil(0.95 * len(cus_list[0].mtime)), len(cus_list[0].mtime)])  # 95分位数

    def convert_qos_constraint(self) -> np.array:
        """
        将边缘节点和客户之间的时延关系qos（Python字典结构）转换为qos_np（Numpy二维数组结构）
        :return:
        """
        qos_np = np.zeros((len(self.cus_list), len(self.sit_list)))
        for i in range(len(self.cus_list)):
            for j in range(len(self.sit_list)):
                qos_np[i][j] = self.qos_dict[self.sit_list[j].name, self.cus_list[i].name]
        return qos_np

    def check_feasible(self) -> bool:
        """
        :return Status: True表示当前Solution为可行解，False为不可行解
        检查当前solution是否为可行解，即满足如下约束：
        （1）x_ijt为非负整数
        （2）客户节点带宽需求只能分配到满足QoS约束的边缘节点
        （3）客户节点需求必须全部分配给边缘节点
        （4）边缘节点接受的带宽需求不能超过其带宽上限
        """
        print("\n开始验证当前解是否为可行解！")

        if isinstance(self.solution, str):
            return NotImplemented

        count = 0  # 记录违背约束的次数

        if np.any(self.solution < 0):
            # raise Exception("不满足约束（1）：x_ijt为非负整数！")
            print(self.solution)
            print("不满足约束（1）：x_ijt为非负整数！")
            count += 1
        print("通过：约束（1）x_ijt为非负整数！")

        for t in range(len(self.mtime_list)):
            sub_solution = self.solution[t]
            for i in range(len(self.cus_list)):
                for j in range(len(self.sit_list)):
                    if self.qos_np[i][j] >= self.qos_constraint and sub_solution[i][j] != 0:
                        print("在时刻{}客户节点{}和边缘节点{}不满足".format(self.mtime_list[t],
                                                             self.cus_list[i].name,
                                                             self.sit_list[j].name), end='')
                        print("约束（2）：客户节点带宽需求只能分配到满足QoS约束的边缘节点！")
                        count += 1
        print("通过：约束（2）客户节点带宽需求只能分配到满足QoS约束的边缘节点！")

        for t in range(len(self.mtime_list)):
            for i in range(len(self.cus_list)):
                sub_solution = self.solution[t][i]
                if sub_solution.sum() != self.cus_list[i].demand[t]:
                    print("在时刻{}客户节点{}不满足".format(self.mtime_list[t], self.cus_list[i].name), end='')
                    print("约束（3）：客户节点需求{}必须全部分配给边缘节点！被满足{}！".format(
                        self.cus_list[i].demand[t], sub_solution.sum()
                    ))
                    count += 1
        print("通过：约束（3）客户节点需求必须全部分配给边缘节点！")

        for t in range(len(self.mtime_list)):
            for j in range(len(self.sit_list)):
                provide = sum(self.solution[t][i][j] for i in range(len(self.cus_list)))
                if provide > self.sit_list[j].band_width:
                    print("在时刻{}边缘节点{}不满足".format(self.mtime_list[t], self.cus_list[j].name), end='')
                    print("约束（4）：边缘节点接受的带宽需求不能超过其带宽上限！为{}".format(provide))
                    count += 1
        print("通过：约束（4）边缘节点接受的带宽需求不能超过其带宽上限！")

        if count == 0:
            print("当前解为可行解！")
            return True
        else:
            print("警告！当前解为不可行解！")
            return False

    def objective(self):
        """
        根据目标函数计算当前solution的目标函数值
        """
        if isinstance(self.solution, str):
            return NotImplemented

        obj_value = 0

        for j in range(len(self.sit_list)):
            w_j_list = []
            for t in range(len(self.mtime_list)):
                w_j_t = sum(self.solution[t][i][j] for i in range(len(self.cus_list)))
                w_j_list.append(w_j_t)
            w_j_list.sort()
            s_j = w_j_list[self.percentile_95 - 1]
            obj_value += s_j
        self.obj_value = obj_value
        print("计算成功！当前解的目标函数值为{}！".format(obj_value))

    def objective_terminated_t(self, terminated_t, j_specific: list) -> int:
        """
        根据目标函数计算当前solution的目标函数值，基于mtime_list[0:terminated_t+1]进
        行计算，若j_specific指定了，则仅仅计算边缘j_specific的边缘节点成本
        """
        mtime_list_specific = self.mtime_list[0:terminated_t+1]
        obj_value = 0
        percentile_95_specific = min([math.ceil(0.95 * len(mtime_list_specific)), len(mtime_list_specific)])
        for j in j_specific:
            w_j_list = []
            for t in range(len(mtime_list_specific)):
                w_j_t = sum(self.solution[t][i][j] for i in range(len(self.cus_list)))
                w_j_list.append(w_j_t)
            w_j_list.sort()
            s_j = w_j_list[percentile_95_specific - 1]
            obj_value += s_j
        return round(obj_value, parameter.decimal)

    def write_to_file(self):
        """
        将当前解决方案写入到文件中
        """
        mtime_list = self.cus_list[0].mtime
        with open(parameter.solution_path, mode='w', encoding='utf-8') as f:
            for t in range(len(mtime_list)):
                for i in range(len(self.cus_list)):
                    f.write(self.cus_list[i].name + ':')
                    if self.cus_list[i].demand == 0:
                        continue
                    str_to_write = ''
                    for j in range(len(self.sit_list)):
                        sol = self.solution[t, i, j]
                        if sol != 0:
                            str_to_write += '<' + self.sit_list[j].name + ',' + str(int(sol)) + '>,'
                    f.write(str_to_write[0:-1])
                    f.write('\n')
        print("\n\n成功将解决方案写入到文件{}!".format(parameter.solution_path))


if __name__ == '__main__':
    print("程序开始！")
