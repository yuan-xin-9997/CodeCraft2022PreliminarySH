# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: CallAlgorithm.py
@time: 2022/3/22 20:54
@description:
"""
import copy
import numpy as np
from Results import Results
from ReadData import read_data
from utils import PriorityQueue, time_this, Parameter

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
    # initial_solution = FlowAssignmentState(cus_list, sit_list, qos_dict, qos_constraint)  # for ALNS 包
    initial_solution = Results(cus_list, sit_list, qos_dict, qos_constraint)

    # 时刻列表
    mtime_list = initial_solution.mtime_list

    # 构建二维数组，表示时刻t边缘节点j被选择的优先级
    p = 1 / len(sit_list)
    select_priority = np.full((len(mtime_list), len(sit_list)), round(p, parameter.decimal))

    # 计算客户节点优先级选择队列输入数据，基于对每个客户节点i，其优先级=能为该客户节点服务的边缘节点数量
    cus_priority_list = []
    # 记录能对客户节点进行服务的边缘节点索引，{i_index:[j_index_1,j_index_2]}
    # cus_serve_by_site = {}
    for i in range(len(cus_list)):
        count = 0
        # cus_serve_by_site[i] = []
        for j in range(len(sit_list)):
            if initial_solution.qos_np[i][j] < initial_solution.qos_constraint:
                count += 1
                # cus_serve_by_site[i].append(j)
        cus_priority_list.append(count)

    # 逐时刻，将边缘节点带宽分配给客户节点
    for t in range(len(mtime_list)):
        print('\n开始为时刻{}安排流量分配计划!'.format(mtime_list[t]))

        # 当前时刻，各个边缘节点剩余可供分配的带宽
        sit_left_supply = [sit_list[j].band_width for j in range(len(sit_list))]

        # 当前时刻，各个客户节点还未满足的带宽
        cus_left_demand = [cus_list[i].demand[t] for i in range(len(cus_list))]

        # 构建客户节点优先级队列，优先级越小的客户节点，在每次时刻迭代中，优先被安排分配流量
        priority_queue_i = PriorityQueue()
        for i in range(len(cus_list)):
            priority_queue_i.put(i, cus_priority_list[i])

        # 构建边缘节点优先级队列，优先级越小的边缘节点，在被分配时候将被优先选择
        priority_queue_j = PriorityQueue()
        for j in range(len(sit_list)):
            priority_queue_j.put(j, select_priority[t][j])

        # 在当前t时刻，按照客户节点优先级越低，逐客户节点分配带宽
        while not priority_queue_i.empty():

            i_index = priority_queue_i.get()
            print('开始为客户节点{}分配流量带宽，其当前时刻带宽需求为{}！'.format(
                cus_list[i_index].name, cus_list[i_index].demand[t]), end='->'
            )

            # 记忆列表，用来记住在给当前客户节点分配带宽之后，依然还剩下带宽需求的边缘节点
            memory_list = []

            # 依次从优先级队列中选择用来服务当前客户节点的边缘节点
            while not priority_queue_j.empty():

                # 客户节点i被满足，则跳出
                if cus_left_demand[i_index] == 0:
                    break

                # 根据优先级队列选择优先级最小的边缘节点用来服务当前客户节点
                j_index = priority_queue_j.get()

                # 若客户节点i和边缘节点j之间的QoS满足给定阈值，则进行分配
                if initial_solution.qos_np[i_index, j_index] < initial_solution.qos_constraint:

                    if cus_left_demand[i_index] < sit_left_supply[j_index]:  # 可被一次性满足
                        initial_solution.solution[t, i_index, j_index] += cus_left_demand[i_index]
                        sit_left_supply[j_index] -= cus_left_demand[i_index]
                        cus_left_demand[i_index] = 0

                        priority = parameter.alpha * (sit_left_supply[j_index] / sum(sit_left_supply)) + \
                                   (1 - parameter.alpha) * select_priority[t][j_index]
                        priority_queue_j.put(j_index, round(priority, parameter.decimal))

                        break

                    if 0 < sit_left_supply[j_index] <= cus_left_demand[i_index]:  # 不可被一次性满足
                        initial_solution.solution[t, i_index, j_index] += sit_left_supply[j_index]
                        cus_left_demand[i_index] -= sit_left_supply[j_index]
                        sit_left_supply[j_index] = 0

                # 否则不分配，并且插入为优先级队列中
                else:
                    priority = parameter.alpha * (sit_left_supply[j_index] / sum(sit_left_supply)) + \
                               (1 - parameter.alpha) * select_priority[t][j_index]
                    memory_list.append((j_index, round(priority, parameter.decimal)))

            # 若遍历完优先级队列，依然无法满足当前客户节点，则应该抛出错误！
            if cus_left_demand[i_index] != 0:
                print("分配失败！")
                raise Exception("无法满足客户节点{}的带宽需求！".format(cus_list[i_index].name))
            else:
                print("分配成功！")

            for memo in memory_list:
                priority_queue_j.put(memo[0], memo[1])

        # # 更新下一时刻边缘节点被选择的优先级
        # if t < len(mtime_list) - 1:
        #     total_cost_to_now = initial_solution.objective_terminated_t(t, [j for j in range(len(sit_list))])
        #     for j in range(len(sit_list)):
        #         total_cost_to_now_j = initial_solution.objective_terminated_t(t, [j]) / total_cost_to_now
        #         select_priority[t + 1, j] = parameter.alpha * total_cost_to_now_j + \
        #                                     (1 - parameter.alpha) * select_priority[t, j]

    # 验证当前解是否为可行解
    if parameter.env != 'norm':
        flag = initial_solution.check_feasible()
        if flag is True:
            initial_solution.objective()  # 计算目标函数值

    # 将结果写入到文件
    initial_solution.write_to_file()

    print('\n初始解生成算法结束！')

    return initial_solution


@time_this
def initial_solution_generation_1(cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):
    """
    基于贪婪启发式算法构建流量分配模型初始解，本函数在上一函数的基础上进行优化，减少对不必要的边缘节点进行分配
    :param cus_list: 客户类对象列表
    :param sit_list: 边缘节点类对象列表
    :param qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :param qos_constraint: 客户节点和边缘节点之间的网络质量
    :return:
    """
    print('\n开始初始解生成算法！')
    # initial_solution = FlowAssignmentState(cus_list, sit_list, qos_dict, qos_constraint)  # for ALNS 包
    initial_solution = Results(cus_list, sit_list, qos_dict, qos_constraint)

    # 时刻列表
    mtime_list = initial_solution.mtime_list

    # 构建二维数组，表示时刻t边缘节点j被选择的优先级
    p = 1 / len(sit_list)
    select_priority = np.full((len(mtime_list), len(sit_list)), round(p, parameter.decimal))

    # 计算客户节点优先级选择队列输入数据，基于对每个客户节点i，其优先级=能为该客户节点服务的边缘节点数量
    cus_priority_list = []
    # 记录能对客户节点进行服务的边缘节点索引，{i_index:[j_index_1,j_index_2]}
    cus_serve_by_site = {}
    for i in range(len(cus_list)):
        count = 0
        cus_serve_by_site[i] = []
        for j in range(len(sit_list)):
            if initial_solution.qos_np[i][j] < initial_solution.qos_constraint:
                count += 1
                cus_serve_by_site[i].append(j)
        cus_priority_list.append(count)

    # 构建客户节点优先级队列，优先级越小的客户节点，在每次时刻迭代中，优先被安排分配流量
    priority_queue_i_for_all = PriorityQueue()
    for i in range(len(cus_list)):
        priority_queue_i_for_all.put(i, cus_priority_list[i])

    # 逐时刻，将边缘节点带宽分配给客户节点
    for t in range(len(mtime_list)):
        print('\n开始为时刻{}安排流量分配计划!'.format(mtime_list[t]))

        # 当前时刻，各个边缘节点剩余可供分配的带宽
        sit_left_supply = [sit_list[j].band_width for j in range(len(sit_list))]

        # 当前时刻，各个客户节点还未满足的带宽
        cus_left_demand = [cus_list[i].demand[t] for i in range(len(cus_list))]

        # 客户节点优先级队列
        priority_queue_i = copy.deepcopy(priority_queue_i_for_all)

        # 在当前t时刻，按照客户节点优先级从低到高，逐客户节点分配带宽
        while not priority_queue_i.empty():

            i_index = priority_queue_i.get()
            print('开始为客户节点{}分配流量带宽，其当前时刻带宽需求为{}！'.format(
                cus_list[i_index].name, cus_list[i_index].demand[t]), end='->'
            )

            # 构建边缘节点选择列表，选择优先级越小越靠后，靠后的边缘节点，在被分配时候将被优先选择
            sit_select_list = []
            for j in cus_serve_by_site[i_index]:
                if sit_left_supply[j] > 0:
                    sit_select_list.append((j, select_priority[t][j]))
            sit_select_list.sort(key=lambda ele: ele[1], reverse=True)

            # 依次从优先级队列中选择用来服务当前客户节点的边缘节点
            while sit_select_list:

                # 客户节点i被满足，则跳出
                if cus_left_demand[i_index] == 0:
                    break

                # 根据优先级队列选择优先级最小的边缘节点（列表最后一个元素）用来服务当前客户节点
                j_index = sit_select_list.pop()[0]

                if cus_left_demand[i_index] < sit_left_supply[j_index]:  # 可被一次性满足
                    initial_solution.solution[t, i_index, j_index] += cus_left_demand[i_index]
                    sit_left_supply[j_index] -= cus_left_demand[i_index]
                    cus_left_demand[i_index] = 0

                    break

                if 0 < sit_left_supply[j_index] <= cus_left_demand[i_index]:  # 不可被一次性满足
                    initial_solution.solution[t, i_index, j_index] += sit_left_supply[j_index]
                    cus_left_demand[i_index] -= sit_left_supply[j_index]
                    sit_left_supply[j_index] = 0

            # 若遍历完优先级队列，依然无法满足当前客户节点，则应该抛出错误！
            if cus_left_demand[i_index] != 0:
                print("分配失败！")
                raise Exception("无法满足客户节点{}的带宽需求！".format(cus_list[i_index].name))
            else:
                print("分配成功！")

        # 更新下一时刻边缘节点被选择的优先级（由于下述代码极其耗时）
        # if t < len(mtime_list) - 1:
        #     total_cost_to_now = initial_solution.objective_terminated_t(t, [j for j in range(len(sit_list))])
        #     for j in range(len(sit_list)):
        #         total_cost_to_now_j = initial_solution.objective_terminated_t(t, [j]) / total_cost_to_now
        #         select_priority[t + 1, j] = parameter.alpha * total_cost_to_now_j + \
        #                                     (1 - parameter.alpha) * select_priority[t, j]

    # 验证当前解是否为可行解
    if parameter.env != 'norm':
        flag = initial_solution.check_feasible()
        if flag is True:
            initial_solution.objective()  # 计算目标函数值

    # 将结果写入到文件
    initial_solution.write_to_file()

    print('\n初始解生成算法结束！')

    return initial_solution


def algorithm(cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):
    """
    基于ALNS启发式算法对流量分配模型进行求解，算法主要逻辑如下：
    0.基于贪婪算法生成初始可行解
    1.移除启发式算法Destroy
        破坏率∈[0.15，0.25]
        每次对当前解移除前0.15*len(sit_list)个边缘节点成本最大
    2.插入启发式算法Repair
        对被移除的0.15*len(sit_list)个边缘节点进行重新分配，采用贪婪启发式算法
    :param cus_list: 客户类对象列表
    :param sit_list: 边缘节点类对象列表
    :param qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :param qos_constraint: 客户节点和边缘节点之间的网络质量
    :return:
    """
    initial_solution = initial_solution_generation(cus_list, sit_list, qos_dict, qos_constraint)

    if parameter.iterations < 0:
        raise ValueError("Negative number of iterations.")

    current_solution = best_solution = initial_solution
    for iteration in range(parameter.iterations):

        pass

    return best_solution


if __name__ == '__main__':
    customer_list, site_list, qos, qos_cons = read_data()
    algorithm(customer_list, site_list, qos, qos_cons)
