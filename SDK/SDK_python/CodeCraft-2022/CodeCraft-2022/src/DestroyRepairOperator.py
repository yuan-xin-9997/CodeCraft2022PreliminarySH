# -*- coding: utf-8 -*-
"""
@author: yuan_xin
@contact: yuanxin9997@qq.com
@file: DestroyRepairOperator.py
@time: 2022/3/27 17:30
@description:
"""
import copy
import random
from Results import Results
from utils import Parameter
parameter = Parameter()
random.seed(42)


def worst_destroy(current_solution: Results):
    """
    TODO：最差破坏启发式算法
    """
    destroyed = copy.deepcopy(current_solution)
    be_destroyed_sit_num = int(parameter.degree_of_destruction * len(current_solution.sit_list))
    be_destroyed_sit_index = random.sample(current_solution.sit_list, be_destroyed_sit_num)
    return destroyed


def random_destroy(current_solution: Results):
    """
    TODO：随机破坏启发式算法
    """
    destroyed = copy.deepcopy(current_solution)
    be_destroyed_sit_num = int(parameter.degree_of_destruction * len(current_solution.sit_list))
    be_destroyed_sit_index = random.sample(current_solution.sit_list, be_destroyed_sit_num)
    for j_index in be_destroyed_sit_index:
        destroyed.solution[]
    return destroyed


def greedy_repair(current_solution, rnd_state):
    """
    TODO：贪婪修复算法
    """
    visited = set(current.edges.values())

    # This kind of randomness ensures we do not cycle between the same
    # destroy and repair steps every time.
    shuffled_idcs = rnd_state.permutation(len(current.nodes))
    nodes = [current.nodes[idx] for idx in shuffled_idcs]

    while len(current.edges) != len(current.nodes):
        node = next(node for node in nodes
                    if node not in current.edges)

        # Computes all nodes that have not currently been visited,
        # that is, those that this node might visit. This should
        # not result in a subcycle, as that would violate the TSP
        # constraints.
        unvisited = {other for other in current.nodes
                     if other != node
                     if other not in visited
                     if not would_form_subcycle(node, other, current)}

        # Closest visitable node.
        nearest = min(unvisited,
                      key=lambda other: distances.euclidean(node[1], other[1]))

        current.edges[node] = nearest
        visited.add(nearest)

    return current
