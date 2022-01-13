from scipy import optimize as op
import numpy as np


def cut_requirement(requirement):
    # the user who only has input or output would not be rebalanced, and the related requirments could be deleted

    while True:
        zin = set()
        zout = set()

        new_requirement = []

        for obj in requirement:
            zin.add(obj[0])
            zout.add(obj[1])

        for obj in requirement:
            if obj[0] in zin and obj[0] in zout and obj[1] in zin and obj[1] in zout:
                new_requirement.append(obj)

        if len(requirement) == len(new_requirement):
            break
        requirement = new_requirement

    return requirement


def linear_proj(requirement):
    # [(from,to,max_amount),...]
    # from = first index = receiver
    # to = second index = sender

    requirement = cut_requirement(requirement)

    if len(requirement) == 0:
        return []

    from_dict = dict()
    to_dict = dict()
    channel_dict = dict()
    node_set = set()
    n = len(requirement)

    func = [-1] * n
    A_ub = None
    B_ub = None
    A_eq = []
    B_eq = []
    zbounds = []

    for obj in requirement:
        a, b, c = obj
        if a not in from_dict:
            from_dict[a] = []
        if b not in to_dict:
            to_dict[b] = []

        from_dict[a].append(b)
        to_dict[b].append(a)

        node_set.add(a)
        node_set.add(b)

        channel_dict[(a, b)] = len(channel_dict)
        zbounds.append((0, c))

    #zbounds = tuple(zbounds)

    for obj in node_set:
        eq = [0] * n
        if obj in from_dict:
            for dst in from_dict[obj]:
                idx = channel_dict[(obj, dst)]
                eq[idx] = -1

        if obj in to_dict:
            for src in to_dict[obj]:
                idx = channel_dict[(src, obj)]
                eq[idx] = 1

        A_eq.append(eq)
        B_eq.append([0])

    # print(func,A_eq,B_eq)

    res = op.linprog(func, A_ub, B_ub, A_eq, B_eq,
                     bounds=zbounds, method='simplex')
    x = res.x

    ans = []
    if res.success:
        for i in range(n):
            if x[i] > 0:
                tmp = (requirement[i][0], requirement[i][1], x[i])
                ans.append(tmp)

    return ans