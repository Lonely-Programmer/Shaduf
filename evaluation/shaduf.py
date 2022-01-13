import networkx as nx
import numpy as np
import random
import collections

within_data = {}
inter_data = {}
all_inter_data = {}
G = None
tx_8 = []

network_file = './network/lightning_simplified_component.edgelist'
payment_value_file = './payment_value/payment_value_satoshi_03.csv'

payment_value_threshold = 466359
tx_load = 50000
repeat = 10


def tuple_sort(a):
    return tuple(sorted(a))


def tuple_trans(a, b):
    a = set(a)  # (0,1)
    b = set(b)  # (0,3)
    common = list(a & b)[0]  # (0,)
    other = list(a ^ b)  # (1,3)
    return (common, min(other), max(other))


def get_within(Alice, Bob):

    # get the balance allocation within channel (Alice, Bob)
    # return (Alice's balance, Bob's balance)

    global within_data

    zchannel = tuple_sort((Alice, Bob))
    if zchannel[0] == Alice:
        return within_data[zchannel]
    elif zchannel[0] == Bob:
        return within_data[zchannel][::-1]


def get_total_amount(Alice):

    # get Alice's total balances in all her channels

    global G

    amt = 0
    for neighbor in G[Alice]:
        amt += get_within(Alice, neighbor)[0]
    return amt


def update_within(Alice, Bob, bal_A, bal_B):

    # for channel (Alice, Bob), update Alice's balance to bal_A and Bob's balance to bal_B

    global within_data

    zchannel = tuple_sort((Alice, Bob))
    if zchannel[0] == Alice:
        within_data[zchannel] = (bal_A, bal_B)
    elif zchannel[0] == Bob:
        within_data[zchannel] = (bal_B, bal_A)
    if bal_A < 0 or bal_B < 0:
        print('wrong channel update')


def get_inter(Alice, Bob, Carol):

    # channel (Alice, Bob) is bound to channel (Bob, Carol) taking Bob as the intermediate, return (amt1, amt2)
    # amt1 is the remaining binding amount for Bob to shift from (Alice, Bob) to (Bob, Carol)
    # amt2 is the remaining binding amount for Bob to shift from (Bob, Carol) to (Alice, Bob)

    global inter_data

    zchannel = tuple_trans((Alice, Bob), (Bob, Carol))
    if zchannel not in inter_data.keys():
        print('no binding')
        return None
    zchannel_inter = inter_data[zchannel]
    if zchannel[1] == Alice:
        return zchannel_inter
    elif zchannel[1] == Carol:
        return zchannel_inter[::-1]


def update_inter(Alice, Bob, Carol, amt1, amt2):

    # update the binding amount between channel (Alice, Bob) and channel (Bob, Carol) to (amt1, amt2)

    global inter_data

    zchannel = tuple_trans((Alice, Bob), (Bob, Carol))
    if zchannel[1] == Alice:
        inter_data[zchannel] = (amt1, amt2)
    elif zchannel[1] == Carol:
        inter_data[zchannel] = (amt2, amt1)
    if amt1 < 0 or amt2 < 0:
        print('wrong inter data')


def get_all_inter(Alice, Bob):

    # get all the channels that is bound to channel (Alice, Bob) taking Alice as the intermediate
    # return the other channel user

    if (Alice, Bob) not in all_inter_data:
        return []
    return all_inter_data[(Alice, Bob)]


def get_max_amt_channel(Alice, Bob):

    # get the maximum of Alice's coins that could be shifted to channel (Alice, Bob) from its bound channels

    amt1 = 0
    all_inter = get_all_inter(Alice, Bob)

    for obj in all_inter:
        zchannel_data_inter = get_inter(obj, Alice, Bob)
        amt2 = zchannel_data_inter[0] # remaining binding amount that could be shifted from (obj, Alice) to (Alice, Bob)

        zchannel_data = get_within(obj, Alice)
        amt3 = zchannel_data[1] # Alice's balance in channel (obj, Alice)

        amt1 += min(amt2, amt3) # the actual amount of coins that could be shifted
    return amt1


def update_max_amt(path, amt):

    # perform the payment

    for i in range(len(path)-1):
        zchannel_data = get_within(path[i], path[i+1])
        if(zchannel_data[0] < amt):
            print('wrong payment')
        update_within(path[i], path[i+1], zchannel_data[0] -
                      amt, zchannel_data[1] + amt)


def update_max_amt_channel(Alice, Bob, amt):

    # shift Alice's coins in other channels to channel (Alice, Bob) until amt coins are collected

    all_inter = get_all_inter(Alice, Bob)

    rebalance_list = dict()

    for obj in all_inter:
        zchannel_data_inter = get_inter(obj, Alice, Bob)
        zchannel_data_within = get_within(obj, Alice)
        rebalance_list[obj] = min(
            zchannel_data_inter[0], zchannel_data_within[1])

    rebalance_list = dict(
        sorted(rebalance_list.items(), key=lambda x: x[1], reverse=True))

    for obj in rebalance_list:
        curr = min(rebalance_list[obj], amt)
        zchannel_data_inter = get_inter(obj, Alice, Bob)
        update_inter(
            obj, Alice, Bob, zchannel_data_inter[0] - curr, zchannel_data_inter[1] + curr)

        zchannel_data_within = get_within(obj, Alice)
        update_within(
            obj, Alice, zchannel_data_within[0], zchannel_data_within[1] - curr)

        zchannel_data_within = get_within(Alice, Bob)
        update_within(
            Alice, Bob, zchannel_data_within[0] + curr, zchannel_data_within[1])

        amt -= curr
        if amt == 0:
            break


def segment_value(x):

    # return the number of bindings

    return int(0.5 * x)


def bind_strategy(mode, node):
    global G

    neighbors = [obj for obj in G[node]]
    degree = len(neighbors)

    if degree == 1:
        return []

    balance_node = dict()
    for obj in neighbors:
        balance_node[obj] = get_within(node, obj)[0]

    balance_high_to_low = dict(
        sorted(balance_node.items(), key=lambda x: x[1], reverse=True))
    balance_low_to_high = collections.OrderedDict(
        reversed(list(balance_high_to_low.items())))
    if mode == 'high-to-low':
        # bind the channel with the highest balance and the channel with the lowest balance, the channel with the second-highest balance and the channel with the second-lowest balance, and so on
        pool = []
        number = segment_value(degree)
        for i in range(number):
            pool.append((list(balance_high_to_low.items())[
                        i][0], list(balance_low_to_high.items())[i][0]))
        return pool

    elif mode == 'random-bind':
        # sample the bindings randomly
        pool1 = []
        for i in range(degree):
            for j in range(i+1, degree):
                pool1.append((i, j))
        number = segment_value(degree)
        pool1 = random.sample(pool1, number)
        pool = []
        for obj in pool1:
            pool.append((neighbors[obj[0]], neighbors[obj[1]]))
        return pool

    elif mode == 'all-bind':
        # bind all pairs of channels
        pool1 = []
        for i in range(degree):
            for j in range(i+1, degree):
                pool1.append((i, j))
        pool = []
        for obj in pool1:
            pool.append((neighbors[obj[0]], neighbors[obj[1]]))
        return pool
    else:
        print('no such mode')
    return []


def bind(mode):
    global G
    znodes = list(G.nodes())
    for node in znodes:
        pool = bind_strategy(mode, node)

        bind_cnt = dict()
        for obj in pool:
            t1 = obj[0]
            t2 = obj[1]
            if t1 not in bind_cnt.keys():
                bind_cnt[t1] = 0
            if t2 not in bind_cnt.keys():
                bind_cnt[t2] = 0
            bind_cnt[t1] += 1
            bind_cnt[t2] += 1
        for t in bind_cnt.keys():
            bal = get_within(node, t)[0]
            bind_cnt[t] = bal // bind_cnt[t]
            # when one channel is bound to multiple channels, the binding amount is equally distributed among them
        for obj in pool:
            t1 = obj[0]
            t2 = obj[1]
            update_inter(t1, node, t2, bind_cnt[t1], bind_cnt[t2])

            if (node, t1) not in all_inter_data.keys():
                all_inter_data[(node, t1)] = []
            if (node, t2) not in all_inter_data.keys():
                all_inter_data[(node, t2)] = []
            all_inter_data[(node, t1)].append(t2)
            all_inter_data[(node, t2)].append(t1)


def initialize(channel_rate, seed):
    global G
    global tx_8
    G = nx.Graph()
    tx_8 = []

    global within_data
    global inter_data
    global all_inter_data
    within_data = {}
    inter_data = {}
    all_inter_data = {}

    random.seed(seed)
    np.random.seed(seed)

    with open(network_file, "r") as f:
        for line in f:
            tmp = line.split()
            nodeA = int(tmp[0])
            nodeB = int(tmp[1])
            capacity = int(int(tmp[2]) * channel_rate)
            G.add_edge(nodeA, nodeB)
            capacity += capacity % 2
            bal_A = capacity // 2
            bal_B = capacity // 2

            if(nodeA < nodeB):
                within_data[((nodeA, nodeB))] = (bal_A, bal_B)
            else:
                within_data[((nodeB, nodeA))] = (bal_B, bal_A)

    with open(payment_value_file, "r") as f:
        for line in f:
            tmp = int(float(line))

            if payment_value_threshold == None:
                if 0 < tmp:
                    tx_8.append(tmp)
            else:
                if 0 < tmp <= payment_value_threshold:
                    tx_8.append(tmp)
    # print('the number of payments:', len(tx_8))
    random.shuffle(tx_8)


def work(method, mode, seed, channel_rate, bind_mode, skew_param):

    initialize(channel_rate, seed)
    if method != 'LN':
        bind(bind_mode)
    znode = list(G.nodes())

    total_tx_number = 0
    success_tx_number = 0
    total_tx_amount = 0
    success_tx_amount = 0

    for i in range(tx_load):

        if(mode == "uniform"):
            while True:
                t1 = random.choice(znode)
                t2 = random.choice(znode)
                if t1 != t2:
                    break

        else:
            while True:
                t1 = len(znode)
                while t1 >= len(znode):
                    t1 = int(np.random.exponential(len(znode)/skew_param))
                # receiver_list = np.random.permutation(znode)
                # receiver_index = len(znode)
                # while receiver_index >= len(znode):
                #     receiver_index = int(
                #         np.random.exponential(len(znode)/skew_param))
                # t2 = receiver_list[receiver_index]
                t2 = random.choice(znode)
                if t1 != t2:
                    break

        path = nx.shortest_path(G, source=t1, target=t2)
        amt = tx_8[i]

        flag = True

        for j in range(len(path)-1):
            z0 = get_within(path[j], path[j+1])[0]
            if z0 >= amt:
                continue
            zmax = amt - z0
            # coins in the bound channels could be shifted to this channel to continue the payment
            if get_max_amt_channel(path[j], path[j+1]) >= zmax:
                update_max_amt_channel(path[j], path[j+1], zmax)  # shift coins
            else:
                flag = False
                break

        if flag:
            success_tx_number += 1
            success_tx_amount += amt
            update_max_amt(path, amt)  # perform the payment

        total_tx_number += 1
        total_tx_amount += amt

    return success_tx_number/total_tx_number, success_tx_amount, total_tx_amount


def uniform_capacity(capacity, method, bind_mode):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s, skew_param=None,
                       channel_rate=capacity, bind_mode=bind_mode, mode='uniform')
        results.append((cur_res))
        print(cur_res)
    ave_result = [0] * len(results[0])
    for i in range(len(results)):
        for j in range(len(results[0])):
            ave_result[j] += (results[i][j] / len(results))

    print('average success ratio:', ave_result[0])
    print('average success volume:', ave_result[1])
    print('average total volume:', ave_result[2])


def test_uniform_capacity(capacity):
    print('performance under uniform payments, varying the channel capacity:')

    for obj in capacity:
        print('capacity factor:', obj)
        print('LN result:')
        uniform_capacity(method="LN", bind_mode=None, capacity=obj)

        print('RB-Shaduf result:')
        uniform_capacity(method="Shaduf", bind_mode='random-bind', capacity=obj)

        print('HL-Shaduf result:')
        uniform_capacity(method="Shaduf", bind_mode='high-to-low', capacity=obj)

        print('AB-Shaduf result:')
        uniform_capacity(method="Shaduf", bind_mode='all-bind', capacity=obj)


def skew(skew_param, method, bind_mode):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s,
                       skew_param=skew_param, channel_rate=10, bind_mode=bind_mode, mode='skew')
        results.append((cur_res))
        print(cur_res)
    ave_result = [0] * len(results[0])
    for i in range(len(results)):
        for j in range(len(results[0])):
            ave_result[j] += (results[i][j] / len(results))

    print('average success ratio:', ave_result[0])
    print('average success volume:', ave_result[1])
    print('average total volume:', ave_result[2])


def test_skew(skew_factor):
    print('performance under skewed payments, varying the skewness factor:')

    for obj in skew_factor:
        print('skewness factor:', obj)
        print('LN result:')
        skew(method="LN", bind_mode=None, skew_param=obj)

        print('HL-Shaduf result:')
        skew(method="Shaduf", bind_mode='high-to-low', skew_param=obj)


def skew_capacity(capacity, method, bind_mode):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s, skew_param=8,
                       channel_rate=capacity, bind_mode=bind_mode, mode='skew')
        results.append((cur_res))
        print(cur_res)
    ave_result = [0] * len(results[0])
    for i in range(len(results)):
        for j in range(len(results[0])):
            ave_result[j] += (results[i][j] / len(results))
    print('average success ratio:', ave_result[0])
    print('average success volume:', ave_result[1])
    print('average total volume:', ave_result[2])


def test_skew_capacity(capacity):
    print('performance under skewed payments, varying the channel capacity:')

    for obj in capacity:
        print('capacity factor:', obj)
        print('LN result:')
        skew_capacity(method="LN", bind_mode=None, capacity=obj)

        print('HL-Shaduf result:')
        skew_capacity(method="Shaduf", bind_mode='high-to-low', capacity=obj)

def main():
    test_uniform_capacity([obj for obj in range(1, 26)])
    test_skew([obj for obj in range(1, 9)])
    test_skew_capacity([obj for obj in range(1, 26)])


if __name__ == "__main__":
    main()
