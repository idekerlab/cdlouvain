#!/usr/bin/env python

import os
import sys
import argparse
import louvain
import igraph


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
        sys.stderr.write('louvain does not support hierarchical clustering with overlapped communities')
        sys.exit()

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
        sys.stderr.write("Not specifying the configuration model; "
                         "perform simple Louvain.")
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
                        sys.stderr.write("negative edge weight not allowed")
                        return 1
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
            sys.stderr.write(str(graph) + ' is not a file')
            return 3
        if os.path.getsize(graph) == 0:
            sys.stderr.write(str(graph) + ' is an empty file')
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
                    sys.stderr.write("negative edge weight not allowed")
                    return 1
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

    if deep == False:
        clusts = partition_to_clust(G, partition)
        if len(clusts) == 0:
            sys.stderr.write("No cluster; Resolution parameter may be too extreme")
            return 1

        maxNode = 0
        for clust in clusts:
            maxNode = max(maxNode, max(clust))

        for i in range(len(clusts)):
            sys.stdout.write(str(maxNode + len(partition) + 1) + ',' + str(maxNode + i + 1) + ',' + 'c-c' + ';')
            for n in clusts[i]:
                sys.stdout.write(str(maxNode + i + 1) + ',' + str(n) + ',' + 'c-m' + ';')
    else:
        partitions = louvain_hierarchy_output(partition)
        clusts_layers = []
        for p in partitions:
            clusts_layers.append(partition_to_clust(G, p))
        if len(clusts_layers[0]) == 0:
            sys.stderr.write("No cluster; Resolution parameter may be too extreme")
            return 1
        maxNode = 0
        for clust in clusts_layers[0]:
            maxNode = max(maxNode, max(clust))
        for i in range(len(clusts_layers[0])):
            for n in clusts_layers[0][i]:
                sys.stdout.write(str(maxNode + i + 1) + ',' + str(n) + ',' + 'c-m' + ';')
        maxNode = maxNode + len(clusts_layers[0])
        for i in range(1, len(clusts_layers)):
            for j in range(len(clusts_layers[i - 1])):
                for k in range(len(clusts_layers[i])):
                    if all(x in clusts_layers[i][k] for x in clusts_layers[i - 1][j]):
                        sys.stdout.write(str(maxNode + k + 1) + ',' + str(
                            maxNode - len(clusts_layers[i - 1]) + j + 1) + ',' + 'c-c' + ';')
                        break
            maxNode = maxNode + len(clusts_layers[i])
        for i in range(len(clusts_layers[-1])):
            sys.stdout.write(str(maxNode + 1) + ',' + str(maxNode - len(clusts_layers[-1]) + i + 1) + ',' + 'c-c' + ';')

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
        sys.stderr.write('Caught exception: ' + str(e))
        return 2


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
