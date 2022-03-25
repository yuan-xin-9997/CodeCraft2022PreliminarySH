# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: CallAlgorithm.py
@time: 2022/3/22 20:54
@description:
"""
import sys
import numpy as np
from Results import Results
from ReadData import read_data, solution_path, Parameter
from utils import PriorityQueue, time_this

parameter = Parameter()


@time_this
def initial_solution_generation(cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):
    """
    基于贪婪启发式算法构建流量分配模型初始解，算法逻辑：
        （1）迭代次数=len(mtime_list)，索引为t，此为外层循环
        （2）记概率p_t_j为在第t此迭代过程中，边缘节点j被选中用来服务当前客户节点i的概率
        （3）每次迭代，逐个遍历客户节点，索引为i，此外内层循环
        （4）每次内层循环，基于每个边缘节点的概率从边缘节点中选择用来服务当前客户节点i，直到
        满足客户节点i的需求（需满足QoS约束和边缘节点供应上限约束）
        （5）外层每次迭代结束，基于式=(边缘节点j截止到目前的95分位带宽值)/(sum边缘节点j截止
        到目前的95分位带宽值)更新p_t_j
    :param cus_list: 客户类对象列表
    :param sit_list: 边缘节点类对象列表
    :param qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :param qos_constraint: 客户节点和边缘节点之间的网络质量
    :return:
    """
    print('\n开始初始解生成算法！')
    # initial_solution = FlowAssignmentState(cus_list, sit_list, qos_dict, qos_constraint)
    initial_solution = Results(cus_list, sit_list, qos_dict, qos_constraint)

    mtime_list = cus_list[0].mtime

    p = 1 / len(sit_list)
    select_prob = np.full((len(mtime_list), len(sit_list)), p)

    for t in range(len(mtime_list)):
        print('\n开始为时刻{}安排流量分配计划!'.format(mtime_list[t]))

        sit_left_supply = []
        for j in range(len(sit_list)):
            sit_left_supply.append(sit_list[j].band_width)

        cus_left_demand = []
        for i in range(len(cus_list)):
            cus_left_demand.append(cus_list[i].demand[t])

        priority_queue = PriorityQueue()
        for j in range(len(sit_list)):
            priority_queue.put(j, select_prob[t][j])

        for i in range(len(cus_list)):
            print('开始为客户节点{}分配流量带宽！'.format(cus_list[i].name))

            memory_list = []

            while not priority_queue.empty():

                if cus_left_demand[i] == 0:
                    break

                j_index = priority_queue.get()

                if qos_dict[sit_list[j_index].name, cus_list[i].name] < qos_constraint:

                    if sit_left_supply[j_index] > cus_left_demand[i]:
                        initial_solution.solution[t, i, j_index] += cus_list[i].demand[t]
                        sit_left_supply[j_index] -= cus_list[i].demand[t]
                        cus_left_demand[i] = 0

                        priority = parameter.alpha * (sit_left_supply[j_index] / sum(sit_left_supply)) + \
                                   (1 - parameter.alpha) * select_prob[t][j_index]
                        priority_queue.put(j_index, priority)

                        break

                    if 0 < sit_left_supply[j_index] <= cus_left_demand[i]:
                        initial_solution.solution[t, i, j_index] += sit_left_supply[j_index]
                        sit_left_supply[j_index] = 0
                        cus_left_demand[i] -= sit_left_supply[j_index]

                else:
                    priority = parameter.alpha * (sit_left_supply[j_index] / sum(sit_left_supply)) + \
                               (1 - parameter.alpha) * select_prob[t][j_index]
                    memory_list.append((j_index, priority))

            if cus_left_demand[i] != 0:
                raise Exception("无法满足客户节点{}的带宽需求！".format(cus_list[i].name))

            for memo in memory_list:
                priority_queue.put(memo[0], memo[1])

        if t < len(mtime_list) - 1:
            total_cost_to_now = initial_solution.objective_terminated_t(t, [j for j in range(len(sit_list))])
            for j in range(len(sit_list)):
                total_cost_to_now_j = initial_solution.objective_terminated_t(t, [j]) / total_cost_to_now
                select_prob[t + 1, j] = parameter.alpha * total_cost_to_now_j + \
                                        (1 - parameter.alpha) * select_prob[t, j]

    flag = initial_solution.check_feasible()
    if flag is True:
        initial_solution.objective()
        initial_solution.write_to_file()

    print('\n初始解生成算法结束！')

    return initial_solution


def algorithm(cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):
    """
    基于ALNS启发式算法对流量分配模型进行求解
    :param cus_list: 客户类对象列表
    :param sit_list: 边缘节点类对象列表
    :param qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :param qos_constraint: 客户节点和边缘节点之间的网络质量
    :return:
    """
    initial_solution = initial_solution_generation(cus_list, sit_list, qos_dict, qos_constraint)

    return


if __name__ == '__main__':
    customer_list, site_list, qos, qos_cons = read_data()
    algorithm(customer_list, site_list, qos, qos_cons)
