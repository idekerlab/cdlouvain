#!/usr/bin/env python

import os
import sys
import argparse
import traceback
import louvain
import igraph

DEFAULT_ERR_MSG = ('Did not get any clusters from Louvain. This could be' +
                   'due to a network that is too connected or ' +
                   ' the resolution parameter is too extreme\n')

def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    help_fm = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_fm)
    parser.add_argument('input',
                        help='Edge file in tab delimited format')
    parser.add_argument('--directed', dest='directed', action='store_true',
                        help='If set, then treat input as a directed graph')
    parser.set_defaults(directed=False)
    parser.add_argument('--configmodel', default='RB',
                        choices=['RB', 'RBER', 'CPM', 'Suprise',
                                 'Significance', 'Default'],
                        help='Configuration model')
    parser.add_argument('--overlap', dest='overlap', action='store_true',
                        help='generate overlapping communities if set')
    parser.set_defaults(overlap=False)
    parser.add_argument('--deep', dest='deep', action='store_true',
                        help='generate hierarchy if set')
    parser.set_defaults(deep=False)
    parser.add_argument('--resolution_parameter', default=0.1, type=float,
                        help='Sets resolution parameter: higher for more clusters')
    parser.add_argument('--seed', default=None, type=int,
                        help='Sets seed for random generator')
    return parser.parse_args(args)


def run_louvain(graph, config_model='Default',
                overlap=False, directed=False, deep=False, interslice_weight=0.1,
                resolution_parameter=0.1, seed=None):
    """
    :outdir: the output directory to comprehend the output link file
    :param graph: input file
    :param config_model: 'RB', 'RBER', 'CPM', 'Surprise', 'Significance'
    :param overlap: bool, whether to enable overlapping community detection
    :param directed
    :param deep
    :param interslice_weight
    :param resolution_parameter
    :return
    """

    if seed != None:
        louvain.set_rng_seed(seed)

    def louvain_hierarchy_output(partition):
        optimiser = louvain.Optimiser()
        partition_agg = partition.aggregate_partition()
        partition_layers = []
        while optimiser.move_nodes(partition_agg) > 0:
            partition.from_coarse_partition(partition_agg)
            partition_agg = partition_agg.aggregate_partition()
            partition_layers.append(list(partition))
        return partition_layers

    def louvain_multiplex(graphs, partition_type, interslice_weight,
                          resolution_parameter):
        layers, interslice_layer, G_full = louvain.time_slices_to_layers(graphs,
                                                                         vertex_id_attr='name',
                                                                         interslice_weight=interslice_weight)
        if partition_type == louvain.ModularityVertexPartition:
            partitions = [partition_type(H) for H in layers]
            interslice_partition = partition_type(interslice_layer, weights='weight')
        else:
            partitions = [partition_type(H, resolution_parameter=resolution_parameter) for H in layers]
            interslice_partition = partition_type(interslice_layer, resolution_parameter=resolution_parameter,
                                                  weights='weight')
        optimiser = louvain.Optimiser()
        optimiser.optimise_partition_multiplex(partitions + [interslice_partition])
        quality = sum([p.quality() for p in partitions + [interslice_partition]])
        return partitions[0], quality

    def partition_to_clust(graphs, partition, min_size_cut=2):
        clusts = []
        node_names = []
        if not isinstance(graphs, list):
            graphs = [graphs]
        for g in graphs:
            node_names.extend(g.vs['name'])
        for i in range(len(partition)):
            clust = [node_names[id] for id in partition[i]]
            clust = list(set(clust))
            if len(clust) < min_size_cut:
                continue
            clust.sort()
            clusts.append(clust)
        clusts = sorted(clusts, key=lambda x: len(x), reverse=True)
        return clusts

    multi = False
    if isinstance(graph, list):
        multi = True

    if overlap == True and multi == False:
        multi = True
        net = graph
        graph = []
        for i in range(4):
            graph.append(net)

    if multi == True and deep == True:
        sys.stderr.write('louvain does not support hierarchical '
                         'clustering with overlapped communities\n')
        return 1

    if config_model == 'RB':
        partition_type = louvain.RBConfigurationVertexPartition
    elif config_model == 'RBER':
        partition_type = louvain.RBERConfigurationVertexPartition
    elif config_model == 'CPM':
        partition_type = louvain.CPMVertexPartition
    elif config_model == 'Surprise':
        partition_type = louvain.SurpriseVertexPartition
    elif config_model == "Significance":
        partition_type = louvain.SignificanceVertexPartition
    else:
        sys.stderr.write("Configuration model not set "
                         "performing simple Louvain.\n")
        partition_type = louvain.ModularityVertexPartition

    weighted = False
    if multi:
        wL = []
        G = []
        for file in graph:
            with open(file, 'r') as f:
                lines = f.read().splitlines()
            elts = lines[0].split()
            if len(elts) == 3:
                weighted = True
            else:
                weighted = False
            for i in range(len(lines)):
                elts = lines[i].split()
                for j in range(2):
                    elts[j] = int(elts[j])
                if weighted == True:
                    elts[2] = float(elts[2])
                    if elts[2] < 0:
                        sys.stderr.write('encountered a negative edge weight '
                                         'on row ' + str(i) + ' (' +
                                         str(lines[i]) + ') which is not allowed\n')
                        return 2
                lines[i] = tuple(elts)
            g = igraph.Graph.TupleList(lines, directed=directed,
                                       weights=weighted)
            G.append(g)
            wL.append(weighted)
            f.close()
        if True in wL and False in wL:
            raise Exception('all graphs should follow the same format')
        if partition_type == louvain.CPMVertexPartition and directed is True:
            raise Exception('graph for CPMVertexPartition must be undirected')
        if partition_type == louvain.SignificanceVertexPartition and weighted is True:
            raise Exception('SignificanceVertexPartition only support '
                            'unweighted graphs')
        partition, quality = louvain_multiplex(G, partition_type,
                                               interslice_weight,
                                               resolution_parameter)

    else:
        if not os.path.isfile(graph):
            sys.stderr.write(str(graph) + ' is not a file\n')
            return 3
        if os.path.getsize(graph) == 0:
            sys.stderr.write(str(graph) + ' is an empty file\n')
            return 4
        with open(graph, 'r') as f:
            lines = f.read().splitlines()
        elts = lines[0].split()
        if len(elts) == 3:
            weighted = True
        else:
            weighted = False

        for i in range(len(lines)):
            elts = lines[i].split()
            for j in range(2):
                elts[j] = int(elts[j])
            if weighted is True:
                elts[2] = float(elts[2])
                if elts[2] < 0:
                    sys.stderr.write('encountered a negative edge weight '
                                     'on row ' + str(i) + ' (' +
                                     str(lines[i]) + ') which is not allowed\n')
                    return 3
            lines[i] = tuple(elts)
        f.close()

        G = igraph.Graph.TupleList(lines, directed=directed, weights=weighted)
        if weighted is False:
            weights = None
        else:
            weights = G.es['weight']
        if partition_type == louvain.ModularityVertexPartition:
            partition = partition_type(G, weights=weights)
        else:
            partition = partition_type(G, weights=weights, resolution_parameter=resolution_parameter)
        if deep == False:
            optimiser = louvain.Optimiser()
            optimiser.optimise_partition(partition)

    lines = []
    if deep == False:
        clusts = partition_to_clust(G, partition)
        if len(clusts) == 0:
            sys.stderr.write(DEFAULT_ERR_MSG)
            return 4

        maxNode = 0
        for clust in clusts:
            maxNode = max(maxNode, max(clust))

        for i in range(len(clusts)):
            lines.append(str(maxNode + len(partition) + 1) + '\t' + str(maxNode + i + 1))
            for n in clusts[i]:
                lines.append(str(maxNode + i + 1) + '\t' + str(n))
    else:
        partitions = louvain_hierarchy_output(partition)
        clusts_layers = []
        for p in partitions:
            clusts_layers.append(partition_to_clust(G, p))
        if len(clusts_layers) == 0:
            sys.stderr.write(DEFAULT_ERR_MSG)
            return 5
        if len(clusts_layers[0]) == 0:
            sys.stderr.write(DEFAULT_ERR_MSG)
            return 6
        maxNode = 0
        for clust in clusts_layers[0]:
            maxNode = max(maxNode, max(clust))
        for i in range(len(clusts_layers[0])):
            for n in clusts_layers[0][i]:
                lines.append(str(maxNode + i + 1) + '\t' + str(n))
        maxNode = maxNode + len(clusts_layers[0])
        for i in range(1, len(clusts_layers)):
            for j in range(len(clusts_layers[i - 1])):
                for k in range(len(clusts_layers[i])):
                    if all(x in clusts_layers[i][k] for x in clusts_layers[i - 1][j]):
                        lines.append(str(maxNode + k + 1) + '\t' + str(maxNode - len(clusts_layers[i - 1]) + j + 1))
                        break
            maxNode = maxNode + len(clusts_layers[i])
        for i in range(len(clusts_layers[-1])):
            lines.append(str(maxNode + 1) + '\t' + str(maxNode - len(clusts_layers[-1]) + i + 1))

    # trim the hierarchy to remove contigs
    up_tree = {}
    down_tree = {}
    for line in lines:
        elts = line.split()
        down_tree.setdefault(elts[0], [])
        down_tree[elts[0]].append(elts[1])
        up_tree.setdefault(elts[1], [])
        up_tree[elts[1]].append(elts[0])

    # store root and leaves
    set1 = set(down_tree.keys())
    set2 = set(up_tree.keys())
    root_l = list(set1.difference(set2))
    leaf_l = list(set2.difference(set1))
    node_l = list(set1.union(set2))

    # find all contigs in the DAG
    Contigs = []
    work_list = root_l
    visited = {}
    for node in node_l:
        visited[node] = 0
    work_path = []
    new_path = False
    while work_list:
        key = work_list.pop(0)
        if new_path == False:
            work_path.append(key)
        else:
            work_path.append(up_tree[key][visited[key]])
            work_path.append(key)
        if key in leaf_l:
            new_path = True
            Contigs.append(work_path)
            work_path = []
        elif len(down_tree[key]) > 1 or visited[key] > 0:
            new_path = True
            Contigs.append(work_path)
            work_path = []
        if visited[key] == 0 and key not in leaf_l:
            work_list = down_tree[key] + work_list
        visited[key] += 1

    # write trimmed DAG
    for path in Contigs[1:]:
        sys.stdout.write(path[0] + ',' + path[-1] + ',')
        if path[-1] in leaf_l:
            sys.stdout.write('c-m' + ';')
        else:
            sys.stdout.write('c-c' + ';')

    sys.stdout.flush()
    return 0


def main(args):
    """
    Main entry point for program
    :param args: command line arguments usually :py:const:`sys.argv`
    :return: 0 for success otherwise failure
    :rtype: int
    """
    desc = """
    Runs louvain on command line, sending output to standard
    out 
    """

    theargs = _parse_arguments(desc, args[1:])

    try:
        inputfile = os.path.abspath(theargs.input)

        return run_louvain(inputfile, config_model=theargs.configmodel, overlap=theargs.overlap,
                           directed=theargs.directed, deep=theargs.deep,
                           resolution_parameter=theargs.resolution_parameter, seed=theargs.seed)

    except Exception as e:
        sys.stderr.write('\n\nCaught exception: ' + str(e))
        traceback.print_exc()
        return 2


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
