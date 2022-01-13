import networkx as nx
import numpy as np
import random
from functools import *
from revive_linear import *

balance_dict = dict()
req_node_set = set()
req_passage_set = set()
req_passage_dict = dict()
G = None
tx_8 = []

network_file = './network/lightning_simplified_component.edgelist'
payment_value_file = './payment_value/payment_value_satoshi_03.csv'

payment_value_threshold = 466359
tx_load = 50000
repeat = 10
node_threshold = 400
channel_threshold = 1500


def get_max_amount(path):

    # get the maximum amount that the path could deliver

    global balance_dict

    ans = 9999999999
    for i in range(len(path)-1):
        tmp = balance_dict[(path[i], path[i+1])]
        ans = min(ans, tmp)

    return ans


def gather_demand(path, amt):

    # when the user has insufficient balance for the payment amt, the user has the demand to shift coins in other channels to this channel to continue the payment

    global balance_dict
    global req_node_set
    global req_passage_set

    for i in range(len(path)-1):
        tmp = balance_dict[(path[i], path[i+1])]
        if tmp < amt:
            req_node_set.add(path[i])
            req_node_set.add(path[i+1])
            req_passage_set.add((path[i], path[i+1]))
            req_passage_set.add((path[i+1], path[i]))


def update_amount(path, amt):

    # perform the payment via the path

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
        gather_demand(path, amt)  # gather the demands
        return False

    update_amount(path, amt)  # perform the payment
    return True


def richness_sort(a, b):

    global balance_dict

    x = balance_dict[a[::-1]]
    y = balance_dict[b[::-1]]

    if x < y:
        return -1
    if x > y:
        return 1
    return 0


def set_objective(path, amt):

    # set the rebalancing objectives for users in the path who lacks coins for the payment amount amt

    global balance_dict
    global req_passage_dict
    global G

    for i in range(len(path)-1):
        tmp = balance_dict[(path[i], path[i+1])]
        if tmp < amt:
            # require_amt coins are requested to shift to path[i] in channel (path[i], path[i+1]) from path[i]'s other channels
            require_amt = amt - tmp
        else:
            # require_amt = 0
            continue

        # skip if the required amount could not be shifted to this channel
        if balance_dict[(path[i+1], path[i])] < require_amt:
            continue

        # skip if the channel has been required by the previous payments
        if (path[i], path[i+1]) in req_passage_dict:
            continue
        if (path[i+1], path[i]) in req_passage_dict:
            continue

        # path[i] is the receiver, path[i+1] is the sender
        req_passage_dict[(path[i], path[i+1])] = require_amt
        # if require_amt == 0:
        #     continue

        # select the channels that coulf shift coins to this channel, i.e., not be required by the previous payments
        candidate_passage = [(obj, path[i])
                             for obj in G[path[i]] if obj != path[i+1]]  # obj is the receiver, path[i] is the sender
        candidate_passage = [
            obj for obj in candidate_passage if obj not in req_passage_dict]
        candidate_passage = [
            obj for obj in candidate_passage if obj[::-1] not in req_passage_dict]
        candidate_passage = sorted(
            candidate_passage, key=cmp_to_key(richness_sort), reverse=True)

        # fail if the sum of user's coins is less than the required amt
        out_total = 0
        for obj in candidate_passage:
            out_total += balance_dict[obj[::-1]]
        if out_total < require_amt:
            del req_passage_dict[(path[i], path[i+1])]
            continue

        # set the rebalancing objectives
        for obj in candidate_passage:
            req_passage_dict[obj] = min(balance_dict[obj[::-1]], require_amt)
            require_amt -= req_passage_dict[obj]

            if require_amt <= 0:
                break


def confirm_demand(suspended_tx):

    # set rebalancing objectives for users

    global req_passage_dict
    global G

    for obj in suspended_tx:
        src, dst, amt = obj
        path = nx.shortest_path(G, source=src, target=dst)
        set_objective(path, amt)

    ans = []
    for obj in req_passage_dict:
        if req_passage_dict[obj] != 0:
            # (receiver, sender, amt)
            ans.append(obj + (req_passage_dict[obj],))

    return ans


def clear_requirement():
    global req_node_set
    global req_passage_set
    global req_passage_dict
    req_node_set = set()
    req_passage_set = set()
    req_passage_dict = dict()


def adjust(project):

    # update the channel balance according to the rebalancing transactions

    global balance_dict

    for obj in project:
        src, dst, amt = obj  # [(receiver,sender,amount)]
        amt = int(amt + 0.5)
        balance_dict[(src, dst)] += amt
        balance_dict[(dst, src)] -= amt

        if balance_dict[(dst, src)] < 0 or balance_dict[(src, dst)] < 0:
            print('wrong rebalancing')


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


def work(channel_rate, mode, method, skew_param, seed):
    global tx_8
    global req_node_set
    global req_passage_set

    initialize(channel_rate, seed)
    clear_requirement()

    znode = list(G.nodes())
    total_tx_number = 0
    total_tx_amount = 0
    success_tx_number = 0
    success_tx_amount = 0
    revive_success = 0
    revive_total = 0

    suspended_tx = []

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

        result = transaction(t1, t2, tx_8[i])
        if result:
            success_tx_number += 1
            success_tx_amount += tx_8[i]
        else:
            suspended_tx.append((t1, t2, tx_8[i]))

        total_tx_number += 1
        total_tx_amount += tx_8[i]

        if method == 'LN':
            continue

        if len(req_node_set) >= node_threshold or len(req_passage_set) >= 2*channel_threshold or i == tx_load - 1:
            revive_total += 1
            requirement = confirm_demand(suspended_tx)
            if len(requirement) > 0:
                project = linear_proj(requirement)  # solve the linear program
            else:
                project = []

            if len(project) > 0:
                revive_success += 1
                # update users' balances according to the rebalancing transactions
                adjust(project)

            for obj in suspended_tx:
                t1, t2, amt = obj
                result = transaction(t1, t2, amt)  # retry the failed payments
                if result:
                    success_tx_number += 1
                    success_tx_amount += amt

            suspended_tx = []
            clear_requirement()

    # if method != 'LN':
    #     print('the number of successful Revive:', revive_success, revive_total,
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
        print('capacity factor:', obj)
        print('LN result:')
        uniform_capacity(method="LN", capacity=obj)

        print('Revive result:')
        uniform_capacity(method="Revive", capacity=obj)


def skew(method, skew_param):
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
        print('skewness factor:', obj)
        print('LN result:')
        skew(method="LN", skew_param=obj)

        print('Revive result:')
        skew(method="Revive", skew_param=obj)


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
        print('capacity factor:', obj)
        print('LN result:')
        skew_capacity(method="LN", capacity=obj)

        print('Revive result:')
        skew_capacity(method="Revive", capacity=obj)


def main():
    test_uniform_capacity([obj for obj in range(1, 26)])
    test_skew([obj for obj in range(1, 9)])
    test_skew_capacity([obj for obj in range(1, 26)])


if __name__ == "__main__":
    main()
