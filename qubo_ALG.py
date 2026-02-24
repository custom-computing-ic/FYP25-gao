from artisan import *
from typedefs import *
from graph_builder import *
import pprint as pp

file_path = 'apps/qubo/cpu.cpp'


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
        self.loop_edges = []
        self.anno_nodes = []
        self.anno_edges = []

    def instrument(self):
        # instrument timer and loop counter for dynamic analysis
        ast_copy = self.ast.clone(changes=False)

        # identify all loops in the program
        results = ast_copy.query("src{Module}")
        # insert artisan header file for code instrumentation
        srcs = results.apply(RSet.distinct, target='src')
        for res in srcs:
            res.src.instrument(Action.before, code="#include <artisan>\n")

        funcs = ast_copy.query("fn{FunctionDecl}")
        for func in funcs:
            fn = func.fn
            ret = fn.rank(context=lambda node: node.isentity("loop"))
        for loop_id in ret:
            loop = ast_copy[loop_id]
            name = loop.id
            ltag = loop.tag

            loop.instrument(Action.before, code='{ artisan::Timer __timer_%s__([](double t) { artisan::Report::write("(0, \'%s\', %%1%%),", t); });'
                        'int __count__%s = 0;' % (ltag, ltag, ltag))
            loop.instrument(Action.begin, code= "__count__%s++;" % ltag)
            loop.instrument(Action.after, code='artisan::Report::write("(1, \'%s\', %%1%%),", __count__%s);}'
                            % (ltag, ltag))
        
        results2 = ast_copy.query("fn{FunctionDecl}", where=lambda fn: fn.name == 'main')

        for res in results2:
            res.fn.instrument(Action.begin,
                code='artisan::Report::connect(); artisan::Report::write("["); int ret;'
                    '{ artisan::Timer __timer_main__([](double t) { artisan::Report::write("(2, %1%)", t); });'
                    '  ret = [] (auto argc, auto argv) { ')
            res.fn.instrument(Action.end,
                code='  }(argc, argv);'
                    '}'
                    'artisan::Report::emit("]");'
                    'artisan::Report::disconnect();'
                    'return ret;')
        
        # commit the instrumented code
        ast_copy.sync(commit=True)
        return ast_copy

    def construct_loop_nodes(self):
        funcs = self.ast.query("fn{FunctionDecl}")
        for func in funcs:
            fn = func.fn
            ret = fn.rank(context=lambda node: node.isentity("loop"))
            for loop_id in ret:
                loop = self.ast[loop_id]
                name = loop.id
                rank = ", ".join([str(x) for x in ret[loop_id]])
                self.ast.pmap[name]['id'] = loop.id
                self.ast.pmap[name]['tag'] = loop.tag
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

                self.loop_nodes.append(LoopNode(loop.id, loop.tag, fn.name, loop.location, loop.entity))

    def run(self):
        self.construct_loop_nodes()
        self.construct_nested_edges()
        self.construct_call_edges()
        ast_copy = self.instrument()

        def report(ast, data):
            self.data = data
        ast_copy.exec(report=report)
        
        self.dynamic_analysis()
    
    def construct_nested_edges(self):
        table = self.ast.query("loop1{loop}={2}>loop2{loop}")
        for row in table:
            outer_node = row['loop1']
            inner_node = row['loop2']
            self.loop_edges.append((outer_node, inner_node, "nested"))


    def construct_call_edges(self):
        table1 = self.ast.query("loop1{loop}=>call_expr{CallExpr}")
        table2 = self.ast.query("loop1{loop}=>loop2{loop}=>call_expr{CallExpr}")
        table2 = [{'loop1': row['loop1'].id, 'call_expr': row['call_expr'].id} for row in table2]
        
        funcs = self.ast.query("fn{FunctionDecl}=>loop{loop}", where=lambda loop: loop.is_outermost())
        table = []
        for row in table1:
            item = {'loop1': row['loop1'].id, 'call_expr': row['call_expr'].id}
            if not item in table2:
                table.append(row)
        
        for row in table:
            children = [child.unparse() for child in row.call_expr.children]

        names = [func['fn'].name for func in funcs]

        for row in table1:
            src = row['loop1']
            if len(row['call_expr'].children) > 0:
                call_func = row['call_expr'].children[0]
                try:
                    if call_func.name in names:
                        targets = [item for item in funcs if item['fn'].name == call_func.name]
                        for item in targets:
                            dst = item['loop']
                            self.loop_edges.append((src, dst, "call"))
                except Exception as e:
                    continue



    def dynamic_analysis(self):
        # extract timer and counter info from data
        timer = [item for item in self.data if item[0] == 0]
        counter = [item for item in self.data if item[0] == 1]

        loop_timer = {}
        loop_counter = {}

        # loop_counter is a dictonary with format: (loop_name, list of iterations for each loop call)
        for item in counter:
            loop_name = item[1]
            if loop_name not in loop_counter:
                loop_counter[loop_name] = [item[2]]
            else:
                loop_counter[loop_name].append(item[2])
        
        for loop in self.loop_nodes:
            id = loop.id
            tag = self.ast.pmap[id]['tag']
            if tag in loop_counter:
                iters = [item[2] for item in counter]
                self.ast.pmap[id]['runtime_min_iter'] = min(iters)
                self.ast.pmap[id]['runtime_max_iter'] = max(iters)
                self.ast.pmap[id]['runtime_avg_iter'] = sum(iters) / len(iters)
            else:
                self.ast.pmap[id]['runtime_min_iter'] = 0
                self.ast.pmap[id]['runtime_max_iter'] = 0
                self.ast.pmap[id]['runtime_avg_iter'] = 0
            print(self.ast.pmap[id])

    def print_pmap(self):
        for vx in self.ast.vertices:
            if len(self.ast.pmap[vx]) > 0:
                print(self.ast.pmap[vx])

                


alg_builder = ALGBuilder(file_path)
alg_builder.run()
# pp.pprint(alg_builder.data, indent=3)
graph = build_hgraph(alg_builder)
alg_builder.print_pmap()
graph.view()


