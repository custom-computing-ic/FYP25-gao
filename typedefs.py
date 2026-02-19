from artisan import *

class LoopNode:
    def __init__(self, id: str, function: str, location: tuple[str, str, str], loop_type: str):
        self.id = id
        self.function = function
        self.location = location
        self.loop_type = loop_type
    
    def print(self):
        print(f"Loop Node {self.id}, function: {self.function}, location: {self.location}, type: {self.loop_type}")


class AnnotatedLoopNode:
    def __init__(self, properties: dict):
        self.id = properties['id']
        self.function = properties['function']
        self.location = properties['location']
        self.loop_type = properties['loop_type']
        
        self.nesting_depth = properties['nesting_depth']
        self.is_innermost = properties['is_innermost']
        self.bound_expression = properties['bound_expression']
        self.bound_static = properties['bound_static']

        self.runtime_min_iter = properties['runtime_min_iter']
        self.runtime_avg_iter = properties['runtime_avg_iter']
        self.runtime_max_iter = properties['runtime_max_iter']
        self.total_dynamic_iterations = properties['total_dynamic_iterations']
        self.dynamic_invocations = properties['dynamic_invocations']
        self.total_time = properties['total_time']
        self.time_per_iteration = properties['time_per_iteration']
        self.percentage_runtime = properties['percentage_runtime']

        self.bytes_read_per_iter = properties['bytes_read_per_iter']
        self.bytes_written_per_iter = properties['bytes_written_per_iter']
        self.access_pattern = properties['access_pattern']
        self.reuse_distance_estimate = properties['reuse_distance_estimate']
        self.working_set_size = properties['working_set_size']
        self.op_counts = properties['op_counts']
        self.arithmetic_intensity = properties['arithmetic_intensity']
        self.reduction_type = properties['reduction_type']
        self.loop_carried_dependency = properties['loop_carried_dependency']
        self.branch_count = properties['branch_count']
        self.branch_entropy = properties['branch_entropy']
        self.scalar_types = properties['scalar_types']
        self.bit_operations = properties['bit_operations']

