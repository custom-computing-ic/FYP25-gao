from heterograph import HGraph

def build_hgraph(alg_builder):
    g = HGraph()
    for vx in alg_builder.ast.vertices:
        if len(alg_builder.ast.pmap[vx]) > 0:
            node_index = g.add_vx()
            alg_builder.ast.pmap[vx]['graph_index'] = node_index
            g.pmap[node_index] = alg_builder.ast.pmap[vx].copy()
    
    for edge in alg_builder.loop_edges:
        outer, inner, edge_type = edge
        outer_index = alg_builder.ast.pmap[outer.id]['graph_index']
        inner_index = alg_builder.ast.pmap[inner.id]['graph_index']
        g.add_edge(outer_index, inner_index)
        g.pmap[(outer_index, inner_index)] = {'edge_type': edge_type}

    # show some node properties in the graph
    g.vstyle = {'label': lambda g, vx: "id:%d|{loop type:%s|avg iter:%d}" %
                                   (vx, g.pmap[vx]['loop_type'], g.pmap[vx]['runtime_avg_iter'])}
    
    # add different visualization for different type of edges
    g.estyle = {'color': lambda g, e: 'blue' if g.pmap[e]['edge_type'] == "nested" else None,
                'label': lambda g, e: g.pmap[e]['edge_type']}

    return g