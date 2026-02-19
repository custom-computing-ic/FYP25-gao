from heterograph import HGraph

def build_hgraph(ast):
    g = HGraph()
    for vx in ast.vertices:
        if len(ast.pmap[vx]):
            node_index = g.add_vx()
            g.pmap[node_index] = ast.pmap[vx].copy()
    g.view()