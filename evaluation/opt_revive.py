import networkx as nx
import numpy as np
import random


G = None
tx_8 = []
revive_total = 0
revive_success = 0
balance_dict = dict()

network_file = './network/lightning_simplified_component.edgelist'
payment_value_file = './payment_value/payment_value_satoshi_03.csv'

payment_value_threshold = 466359
tx_load = 50000
repeat = 10


def opt_revive(sender, receiver, amt):

    # shift sender's coins to channel (sender, receiver) from sender's other channels to continue the payment

    global G
    global balance_dict
    
    channels = dict()
    total_amt = 0

    if balance_dict[(sender, receiver)] + balance_dict[(receiver, sender)] < amt: 
        return False  #the required amount could not be shifted to this channel

    removed_edges = [] 

    for neighbor in G[sender]:
        removed_edges.append((neighbor, sender)) # sender's channels
        if neighbor != receiver:
            channels[neighbor] = balance_dict[(sender, neighbor)]
            total_amt += balance_dict[(sender, neighbor)]

    if total_amt + balance_dict[(sender, receiver)] < amt: # sender's off-chain balances are insufficient for the payment
        return False

    to_be_revived_amount = amt - balance_dict[(sender, receiver)]

    channels = dict(sorted(channels.items(), key=lambda x: x[1], reverse=True))
    total_path = dict()
    i = 0 
    
    # for each sender' channel (sender, obj), find the shortest path from obj to receiver to shift coins, composing the cycle sender-obj-(-path-)-receiver-sender
    # the path would not pass sender's channels
    # payments in these cycles are executed atomically, i.e., the sender either collects sufficient coins, or balances in sender's channels remain unchanged 
    
    G.remove_node(sender)

    for key in channels:
        if to_be_revived_amount <= 0:
            break
        
        if nx.has_path(G, source=key, target=receiver) == False:
            continue
        
        path = nx.shortest_path(G, source=key, target=receiver)
        zmax = get_max_amount(path)

        a = min(to_be_revived_amount, channels[key], zmax)

        for i in range(len(path)-1):

            # path[i] is required to send coins to path[i+1]

            if (path[i], path[i+1]) in total_path:
                # cycles may have overlapping channels
                total_path[(path[i], path[i+1])] += a
            else:
                total_path[(path[i], path[i+1])] = a

        total_path[(sender, key)] = a

        to_be_revived_amount -= a

    if to_be_revived_amount > 0:  # required coins could not be collected
        for obj in removed_edges:
            G.add_edge(obj[0], obj[1])
        return False

    total_path[(receiver, sender)] = amt - balance_dict[(sender, receiver)]

    for obj in removed_edges:
        G.add_edge(obj[0], obj[1])

    for obj in total_path:

        if balance_dict[obj] < total_path[obj]:
            return False

    for obj in total_path:
        balance_dict[obj] -= total_path[obj]
        balance_dict[obj[::-1]] += total_path[obj]
        

    return True


def opt_revive_transaction(src, dst, amt):
    global G
    global balance_dict
    global revive_total
    global revive_success

    path = nx.shortest_path(G, source=src, target=dst)
    undo = []

    for i in range(len(path) - 1):
        tmp = balance_dict[(path[i], path[i+1])]
        if tmp >= amt:
            balance_dict[(path[i], path[i+1])] -= amt
            # to guarantee the completion of the payment, these coins could not be utilized in others' rebalancing
            undo.append((path[i], path[i+1]))
            continue

        revive_total += 1
        simbol = opt_revive(path[i], path[i+1], amt)

        if simbol:
            balance_dict[(path[i], path[i+1])] -= amt
            # to guarantee the completion of the payment, these coins could not be utilized in others' rebalancing
            undo.append((path[i], path[i+1]))
            revive_success += 1
        else:
            for obj in undo:
                balance_dict[obj] += amt
                    
            return False

    for obj in undo:
        balance_dict[obj[::-1]] += amt


    return True


def get_max_amount(path):
    global balance_dict

    ans = 9999999999
    for i in range(len(path)-1):
        tmp = balance_dict[(path[i], path[i+1])]
        ans = min(ans, tmp)

    return ans


def update_amount(path, amt):
    global balance_dict

    for i in range(len(path)-1):
        balance_dict[(path[i], path[i+1])] -= amt
        balance_dict[(path[i+1], path[i])] += amt
        if balance_dict[(path[i], path[i+1])] < 0 or balance_dict[(path[i+1], path[i])] < 0:
            print('wrong payment')


def transaction(src, dst, amt):
    global G

    path = nx.shortest_path(G, source=src, target=dst)
    zmax = get_max_amount(path)
    if zmax < amt:
        return False

    update_amount(path, amt)
    return True


def initialize(channel_rate, seed):
    global G
    global balance_dict
    global tx_8

    G = nx.Graph()
    balance_dict = dict()
    tx_8 = []

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

            balance_dict[(nodeA, nodeB)] = capacity // 2
            balance_dict[(nodeB, nodeA)] = capacity // 2

    with open(payment_value_file, "r") as f:
        for line in f:
            tmp = int(float(line))

            if payment_value_threshold == None:
                if 0 < tmp:
                    tx_8.append(tmp)
            else:
                if 0 < tmp <= payment_value_threshold:
                    tx_8.append(tmp)

    random.shuffle(tx_8)


def work(mode, method, skew_param, channel_rate, seed):
    global tx_8
    global revive_total
    global revive_success

    initialize(channel_rate, seed)
    znode = list(G.nodes())

    success_tx_number = 0
    success_tx_amount = 0
    total_tx_number = 0
    total_tx_amount = 0
    revive_success = 0
    revive_total = 0

    for i in range(tx_load):

        if mode == 'uniform':
            while True:
                t1 = random.choice(znode)
                t2 = random.choice(znode)
                if t1 != t2:
                    break

        elif mode == 'skew':
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

        else:
            print("No such mode:", mode)
            return

        if method == 'LN':
            result = transaction(t1, t2, tx_8[i])

        else:
            result = opt_revive_transaction(t1, t2, tx_8[i])

        if result:
            success_tx_number += 1
            success_tx_amount += tx_8[i]

        total_tx_number += 1
        total_tx_amount += tx_8[i]

    # if method != 'LN':
    #     print('the number of successful OPT-Revive:', revive_success, revive_total,
    #           revive_success / revive_total)

    return success_tx_number / total_tx_number, success_tx_amount, total_tx_amount


def uniform_capacity(capacity, method):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s, skew_param=None,
                       channel_rate=capacity, mode='uniform')
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
        print('capacity factor', obj)
        print('LN result:')
        uniform_capacity(method="LN", capacity=obj)

        print('OPT-Revive result:')
        uniform_capacity(method="OPT-Revive", capacity=obj)


def skew(skew_param, method):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s, skew_param=skew_param,
                       channel_rate=10, mode='skew')
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
        print('skewness factor', obj)
        print('LN result:')
        skew(method="LN", skew_param=obj)

        print('OPT-Revive result:')
        skew(method="OPT-Revive", skew_param=obj)



def skew_capacity(capacity, method):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s, skew_param=8,
                       channel_rate=capacity, mode='skew')
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
        print('capacity factor', obj)
        print('LN result:')
        skew_capacity(method="LN", capacity=obj)

        print('OPT-Revive result:')
        skew_capacity(method="OPT-Revive", capacity=obj)


def main():

    test_uniform_capacity([obj for obj in range(1, 26)])
    test_skew([obj for obj in range(1, 9)])
    test_skew_capacity([obj for obj in range(1, 26)])


if __name__ == "__main__":
    main()
