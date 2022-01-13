#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import networkx as nx
import numpy as np

value = []


def createGraphDump(filename):
    G = nx.Graph()
    for file in filename:
        with open(file, 'r') as f:
            for line in f:
                tmp = line.split()
                for i in range(len(tmp)):
                    if tmp[i][1:-2] == 'block':
                        close_block = tmp[i+1][:-1]
                        block_l = i+1
                        break

                for i in range(block_l, len(tmp)):
                    if tmp[i][1:-2] == 'block':
                        open_block = tmp[i+1][:-1]
                        break
                if int(open_block) > 677167:
                    continue
                if close_block != 'null' and int(close_block) <= 677167:
                    continue  # not closed or closed after 2021-03-31 23:57

                cap = int(tmp[1])
                n1 = tmp[2][2:-2]
                n2 = tmp[3][1:-2]

                if cap <= 0:
                    continue
                if(G.has_edge(n1, n2)):
                    G[n1][n2]['capacity'] = G[n1][n2]['capacity'] + cap
                else:
                    G.add_edges_from([(n1, n2, {'capacity': cap})])

    return G


def createGraph(filename):
    G = nx.Graph()
    for file in filename:
        with open(file, 'r') as f:
            data = json.load(f)
            for i in range(len(data)):
                if data[i]['open']['block'] > 677167:
                    continue

                if data[i]['close']['block'] != None and data[i]['close']['block'] <= 677167:
                    continue  # not closed or closed after 2021-03-31 23:57

                n1 = data[i]['nodes'][0]
                n2 = data[i]['nodes'][1]
                cap = data[i]['satoshis']
                if cap <= 0:
                    continue
                if(G.has_edge(n1, n2)):
                    G[n1][n2]['capacity'] = G[n1][n2]['capacity'] + cap # merge the multiple channels between two users into one channel
                else:
                    G.add_edges_from([(n1, n2, {'capacity': cap})])

    return G


def graphStatics(graph):
    print('nodes:', len(graph.nodes()))
    print('edges:', len(graph.edges()))

    single_channel_user = 0
    for node in graph.nodes():
        if graph.degree(node) == 1:
            single_channel_user += 1
    print('number of single-channel user:', single_channel_user, len(graph.nodes()),
          single_channel_user / len(graph.nodes()))

    capacity = []
    for edge in graph.edges():
        capacity.append(graph[edge[0]][edge[1]]['capacity'])
    capacity = np.array(capacity)
    print('max, min, mean, median, var of capacity:', np.max(capacity), np.min(
        capacity), np.mean(capacity), np.median(capacity), np.var(capacity))


def reassignGraph(graph):
    # change the user's pubkey identifier to a numeric identifier
    nodes = sorted(graph.nodes())
    assign = {}
    for i in range(len(nodes)):
        assign[nodes[i]] = i
    return nx.relabel_nodes(graph, assign)


def main():

    G = createGraph(['channel_1_600000.json', 'channel_600001_677167.json'])
    graphStatics(G)

    nx.write_edgelist(G, 'lightning.edgelist', data=['capacity'])

    G_simplified = reassignGraph(G)
    nx.write_edgelist(
        G_simplified, 'lightning_simplified.edgelist', data=['capacity'])

    G_component = list(G.subgraph(c) for c in nx.connected_components(G))[
        0]  # the largest component
    nx.write_edgelist(reassignGraph(
        G_component), 'lightning_simplified_component.edgelist', data=['capacity'])

    graphStatics(G_component)

main()
