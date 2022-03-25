# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: CallSolver.py
@time: 2022/3/21 19:53
@description:
"""

import math
import sys

import numpy as np
from gurobipy import *
from gurobipy import GRB
from ReadData import read_data, solution_path
from Results import Results


def construct_scheduling_model(cus_list: list, sit_list: list, qos_dict: dict, qos_constraint: int):
    """
    基于Gurobi构建流量分配模型，并调用Gurobi进行求解
    :param cus_list: 客户类对象列表
    :param sit_list: 边缘节点类对象列表
    :param qos_dict: 边缘节点和客户之间的时延字典，键(site_name, customer_name)，值qos_value
    :param qos_constraint: 客户节点和边缘节点之间的网络质量
    :return:
    """
    # 创建Gurobi模型
    m = Model("flow_scheduling_model")

    # 定义变量

    # x_{ijt}: 用 𝑋 表示一组流量分配方案，即 𝑡 时刻第 𝑖 个客户节点向第 𝑗 个
    # 边缘节点分配的带宽为 𝑋𝑖𝑗𝑡 (1 ≤ 𝑖 ≤ 𝑀, 1 ≤ 𝑗 ≤ 𝑁，𝑡 ∈ 𝑇)。
    x_index = {}
    mtime_list = cus_list[0].mtime
    for t in range(len(mtime_list)):
        for i in range(len(cus_list)):
            for j in range(len(sit_list)):
                x_index[cus_list[i].name, sit_list[j].name, mtime_list[t]] = 0
    x = m.addVars(x_index.keys(), lb=0, vtype=GRB.INTEGER, name='x')

    # w_{j, t}: 第 𝑗 个边缘节点在 𝑡 时刻的总带宽需求
    w_index = {}
    for j in range(len(sit_list)):
        for t in mtime_list:
            w_index[sit_list[j].name, t] = 0
    w = m.addVars(w_index, lb=0, vtype=GRB.INTEGER, name='w')

    # u_{j, t1, t2}: 第 j 个边缘节点，若在t1时刻的总带宽需求，大于等于，在t2时刻的总带宽需求，则为1，否则为0，t1可等于t2
    u_index = {}
    for j in range(len(sit_list)):
        for t1 in mtime_list:
            for t2 in mtime_list:
                u_index[sit_list[j].name, t1, t2] = 0
    u = m.addVars(u_index, vtype=GRB.BINARY, name='u')

    # s_j：对所有 𝑡 ∈ 𝑇，边缘节点 𝑗 的 95 百分位带宽值
    s_index = {}
    for j in range(len(sit_list)):
        s_index[sit_list[j].name] = 0
    s = m.addVars(s_index, lb=0, vtype=GRB.INTEGER, name='s')

    # v_{j, t}：若v_{j,t}=1，则s_j=w_{j,t}，否则为0，不成立
    v_index = {}
    for j in range(len(sit_list)):
        for t in mtime_list:
            v_index[sit_list[j].name, t] = 0
    v = m.addVars(v_index, vtype=GRB.BINARY, name='v')

    # 构建约束

    # （2）客户节点带宽需求只能分配到满足 QoS 约束的边缘节点
    for i in range(len(cus_list)):
        for j in range(len(sit_list)):
            if qos_dict[sit_list[j].name, cus_list[i].name] >= qos_constraint:
                for t in mtime_list:
                    m.addConstr(x[cus_list[i].name, sit_list[j].name, t] == 0,
                                name='(2)_%s_%s_%s' % (
                                    cus_list[i].name, sit_list[j].name, t
                                ))

    # （3）客户节点带宽需求必须全部分配给边缘节点
    for t in mtime_list:
        for i in range(len(cus_list)):
            ind = cus_list[i].mtime.index(t)
            m.addConstr(
                x.sum(cus_list[i].name, '*', t) == cus_list[i].demand[ind], name='(3)_%s_%s' % (
                    t, cus_list[i].name
                )
            )

    # （4）边缘节点接收的带宽需求不能超过其带宽上限
    for t in mtime_list:
        for j in range(len(sit_list)):
            m.addConstr(x.sum('*', sit_list[j].name, t) <= sit_list[j].band_width, name='(4)_%s_%s' % (
                t, sit_list[j].name
            ))

    # （5）定义变量w
    for j in range(len(sit_list)):
        for t in range(len(mtime_list)):
            m.addConstr(w[sit_list[j].name, mtime_list[t]] == x.sum('*', sit_list[j].name, mtime_list[t]),
                        name='(5)_%s_%s' % (sit_list[j].name, mtime_list[t]))

    # （6）定义变量u
    for j in range(len(sit_list)):
        # 同一边缘节点，所有时刻变量值相加等于，1+2+...+len(时刻列表)
        # m.addConstr(u.sum(sit_list[j].name, '*') == sum(i for i in range(1, len(mtime_list) + 1)))
        for t1 in range(len(mtime_list)):
            for t2 in range(t1, len(mtime_list)):
                m.addGenConstrIndicator(
                    u[sit_list[j].name, mtime_list[t1], mtime_list[t2]],
                    True,
                    w[sit_list[j].name, mtime_list[t1]] - w[sit_list[j].name, mtime_list[t2]],
                    GRB.GREATER_EQUAL,
                    0,
                    name='(6)_%s_%s_%s' % (sit_list[j].name, mtime_list[t1], mtime_list[t2])
                )

    # （7）定义变量v和s
    percentile_95 = math.ceil(0.95 * len(mtime_list))
    for j in range(len(sit_list)):
        m.addConstr(
            v.sum(sit_list[j].name, '*') == 1, name='(7.2)_%s' % (sit_list[j].name)
        )
        for t in range(len(mtime_list)):
            m.addGenConstrIndicator(
                v[sit_list[j].name, mtime_list[t]],
                True,
                s[sit_list[j].name] - w[sit_list[j].name, mtime_list[t]],
                GRB.EQUAL,
                0,
                name='(7.1)_%s_%s' % (sit_list[j].name, mtime_list[t])
            )
            m.addGenConstrIndicator(
                v[sit_list[j].name, mtime_list[t]],
                True,
                u.sum(sit_list[j].name, mtime_list[t], '*'),
                GRB.EQUAL,
                percentile_95,
                name='(7.3)_%s_%s' % (sit_list[j].name, mtime_list[t])
            )

    # 构建目标函数
    total_cost = 0
    for j in range(len(sit_list)):
        total_cost += s[sit_list[j].name]
    m.setObjective(total_cost, GRB.MINIMIZE)
    m.update()

    # 求解模型
    m.optimize()

    # 打印解，并将解决方案写入到文件中
    if m.status == GRB.OPTIMAL:

        # 打印解决方案
        for t in range(len(mtime_list)):
            for i in range(len(cus_list)):
                for j in range(len(sit_list)):
                    if x[cus_list[i].name, sit_list[j].name, mtime_list[t]].x != 0:
                        print('%s-%s-%s: %s' % (
                            mtime_list[t],
                            cus_list[i].name,
                            sit_list[j].name,
                            x[cus_list[i].name, sit_list[j].name, mtime_list[t]].x))
        print('\n\n最优解: %g' % m.objVal)

        # 将解决方案写入到文件中
        with open(solution_path, mode='w', encoding='utf-8') as f:
            for t in range(len(mtime_list)):
                for i in range(len(cus_list)):
                    f.write(cus_list[i].name + ':')
                    if cus_list[i].demand == 0:
                        continue
                    str_to_write = ''
                    for j in range(len(sit_list)):
                        if x[cus_list[i].name, sit_list[j].name, mtime_list[t]].x != 0:
                            str_to_write += '<' + sit_list[j].name + ',' + str(int(x[cus_list[i].name,
                                                                                     sit_list[j].name,
                                                                                     mtime_list[t]].x)) + '>,'
                    f.write(str_to_write[0:-1])
                    f.write('\n')
            print("\n\n成功将解决方案写入到文件{}!".format(solution_path))

        # 检查Gurobi求解的结果是否满足题目要求
        results = Results(cus_list, sit_list, qos_dict, qos_constraint)
        # results.solution = np.zeros((len(mtime_list), len(cus_list), len(sit_list)))
        for t in range(len(mtime_list)):
            for i in range(len(cus_list)):
                for j in range(len(sit_list)):
                    results.solution[t][i][j] = int(x[cus_list[i].name, sit_list[j].name, mtime_list[t]].x)
        status = results.check_feasible()
        if status is False:
            sys.exit("探测到不可行解，系统退出！")
        else:
            print("检测通过，满足所有约束！")

    elif m.status == GRB.INFEASIBLE:
        print("模型无解！")
        m.computeIIS()
        print('\nThe following constraint cannot be satisfied:')
        for c in m.getConstrs():
            if c.IISConstr:
                print('%s' % c.constrName)
    else:
        print("未知错误！")


if __name__ == '__main__':
    customer_list, site_list, qos, qos_cons = read_data()
    construct_scheduling_model(customer_list, site_list, qos, qos_cons)
