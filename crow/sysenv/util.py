__all__=['ranks_to_nodes_ppn']

def ranks_to_nodes_ppn(max_per_node,ranks):
    """!Given an MPI process that requires "ranks" ranks, and must run on
    compute nodes with max_per_node maximum ranks per node, returns a
    list of (nodes, ranks_per_node) tuples that spread the ranks on as
    few nodes as possible.  No more than two nodes are returned.    """
    if ranks<0:
        raise ValueError('Must have at least 1 MPI rank.')
    if max_per_node<1:
        raise ValueError('Nodes must support at least 1 rank per node.')
    if ranks<max_per_node: # Special case: fewer ranks than size of node
        return [ ( 1, ranks ) ]

    nodes=(ranks+max_per_node-1)//max_per_node
    extra_ranks=nodes*max_per_node-ranks

    if extra_ranks:
        return [ ( nodes-extra_ranks, max_per_node ),
                 ( extra_ranks, max_per_node-1 ) ]
    else :
        return [ ( nodes, max_per_node ) ]

def test():
    assert([(10, 10), (1, 9)] == ranks_to_nodes_ppn(10,109))
    assert([(2,3),(2,2)] == ranks_to_nodes_ppn(3,10))
    assert([(3,1)] == ranks_to_nodes_ppn(10,3))
