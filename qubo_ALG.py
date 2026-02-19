from artisan import *
from typedefs import *
from hgraph import *

file_path = 'apps/qubo/cpu.cpp'
# file_path = 'loop_test.cpp'


def check_constant(nodes):
    if len(nodes) == 0:
        return False
    for node in nodes:
        if node.isentity("IntegerLiteral"):
            continue
        if node.isentity("CallExpr") or node.isentity("DeclRefExpr"):
            # if it's a function call, cannot be constant
            return False
        if node.isentity("BinaryOperator") or node.isentity("UnaryOperator"):
            # check all children of the uop/binop
            return check_constant(node.children)

    return True

class ALGBuilder:
    def __init__(self, cmd=None):
        self.ast = Ast(cmd, parse=False).clone()
        self.data = None
        self.loop_nodes = []
        self.loop_edges = None
        self.anno_nodes = []
        self.anno_edges = None

    def run(self):
        results = self.ast.query("l{loop}")
        funcs = self.ast.query("fn{FunctionDecl}")
        for func in funcs:
            fn = func.fn
            ret = fn.rank(context=lambda node: node.isentity("loop"))
            for loop_id in ret:
                loop = self.ast[loop_id]
                name = loop.id
                rank = ", ".join([str(x) for x in ret[loop_id]])
                self.ast.pmap[name]['id'] = loop.id
                self.ast.pmap[name]['function'] = fn.name
                self.ast.pmap[name]['location'] = loop.location
                self.ast.pmap[name]['loop_type'] = loop.entity

                self.ast.pmap[name]['nesting_depth'] = len(ret[loop_id])
                self.ast.pmap[name]['is_innermost'] = loop.is_innermost()

                try:
                    # loop pattern for(;;) causes errors?
                    self.ast.pmap[name]['bound_expression'] = loop.condition
                    
                    if loop.condition.isentity("CxxBoolLiteralExpr"):
                        self.ast.pmap[name]['bound_static'] = True
                    else:
                        if loop.isentity("ForStmt"):
                            self.ast.pmap[name]['bound_static'] = check_constant([loop.condition.children[1]])
                        else:
                            self.ast.pmap[name]['bound_static'] = check_constant(loop.condition.children)
                except Exception as e:
                    self.ast.pmap[name]['bound_expression'] = None
                    self.ast.pmap[name]['bound_static'] = False


                self.loop_nodes.append(LoopNode(loop.id, fn.name, loop.location, loop.entity))


alg_builder = ALGBuilder(file_path)
alg_builder.run()
build_hgraph(alg_builder.ast)

# check loop nodes
# for node in alg_builder.loop_nodes:
#     node.print()

# for vx in alg_builder.ast.vertices:
#     if len(alg_builder.ast.pmap[vx]):
#         print(f"vertex {vx} pmap => {alg_builder.ast.pmap[vx]}")
