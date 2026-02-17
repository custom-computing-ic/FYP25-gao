# Annotated Loop Graph (ALG)

## 1. Overview

The Annotated Loop Graph (ALG) is a structural abstraction of a program
that captures its **repetition topology** and the hardware-relevant
properties of repetitive computation.

An ALG does not encode full program semantics. Instead, it represents:

-   Where repetition occurs (loops)
-   How repetition propagates (nesting and calls)
-   What workload characteristics are associated with each loop
-   How repetition scales dynamically

ALG is defined formally as:

ALG(P) = (L, E, A_L, A_E)

Where:

-   L = set of loop nodes
-   E = set of typed directed edges between loops
-   A_L = annotation mapping for loop nodes
-   A_E = annotation mapping for loop edges

ALG captures:

Repetition Structure + Execution Weight + Static Constraints

It is:

-   Independent of hardware target
-   Independent of optimization strategy
-   Sufficient to drive heterogeneous acceleration decisions

It does not encode full program semantics, only scalable computation
topology.


------------------------------------------------------------------------

# 2. Formal Definition

## 2.1 Loop Nodes

Each loop node ℓ ∈ L corresponds to a syntactic loop construct:

ℓ = (id, function, location, loop_type)

Where:

-   id: unique identifier
-   function: enclosing function
-   location: (file, line, column)
-   loop_type ∈ {for, while, do-while}

------------------------------------------------------------------------

## 2.2 Edge Set

E ⊆ L × L × T

T = { nest, call }

### Nest Edge

(ℓ_i, ℓ_j, nest) iff ℓ_j is syntactically nested inside ℓ_i in the AST.

Extraction Method (Static): - For each pair of loops: - If ℓ_i is
ancestor of ℓ_j in AST → add nest edge.

### Call Edge

(ℓ_i, ℓ_j, call) iff ℓ_i contains a function call to a function
containing ℓ_j.

Extraction Method (Static): - For each loop ℓ_i: - Identify function
calls inside its body. - Resolve callee. - If callee contains loops ℓ_j
→ add call edge.

------------------------------------------------------------------------

# 3. Node Annotations (A_L)

Below is a comprehensive table of loop node annotations.

  --------------------------------------------------------------------------------
  Annotation                 Static/Dynamic          Extraction Method
  -------------------------- ----------------------- -----------------------------
  loop_id                    Static                  Assigned during AST traversal

  function_name              Static                  Read from enclosing AST node

  loop_type                  Static                  AST node type

  nesting_depth              Static                  Count ancestors in AST

  is_innermost               Static                  Check if no nested loop
                                                     descendants

  bound_expression           Static                  Extract loop condition
                                                     expression

  bound_static               Static                  Determine if bound depends
                                                     only on constants

  runtime_min_iter           Dynamic                 Instrument loop counter,
                                                     track minimum

  runtime_avg_iter           Dynamic                 Instrument loop counter,
                                                     compute average

  runtime_max_iter           Dynamic                 Instrument loop counter,
                                                     track maximum

  total_dynamic_iterations   Dynamic                 Increment counter each
                                                     iteration

  dynamic_invocations        Dynamic                 Increment counter each loop
                                                     entry

  total_time                 Dynamic                 Insert timers before/after
                                                     loop

  time_per_iteration         Derived                 total_time /
                                                     total_dynamic_iterations

  percentage_runtime         Derived                 total_time / program_time

  bytes_read_per_iter        Static/Dynamic          Static: analyze memory
                                                     accesses; Dynamic: hardware
                                                     counters

  bytes_written_per_iter     Static/Dynamic          Same as above

  access_pattern             Static                  Analyze index expressions
                                                     (stride, indirect, etc.)

  reuse_distance_estimate    Static                  Symbolic dependence + access
                                                     range

  working_set_size           Derived                 Unique memory touched per
                                                     iteration

  op_counts                  Static                  Count arithmetic ops in loop
                                                     body

  arithmetic_intensity       Derived                 op_counts / memory traffic

  reduction_type             Static                  Detect associative
                                                     accumulation pattern

  loop_carried_dependency    Static                  Dependence analysis
                                                     (RAW/WAR/WAW)

  branch_count               Static                  Count branch nodes inside
                                                     loop

  branch_entropy             Dynamic                 Profile branch outcomes

  scalar_types               Static                  Inspect variable types

  bit_operations             Static                  Detect bitwise ops
  --------------------------------------------------------------------------------

------------------------------------------------------------------------

# 4. Edge Annotations (A_E)

Edge annotations describe repetition propagation.

  ------------------------------------------------------------------------------------
  Annotation                     Static/Dynamic          Extraction Method
  ------------------------------ ----------------------- -----------------------------
  edge_type (nest/call)          Static                  Determined during graph
                                                         construction

  call_site_count                Static                  Count calls inside parent
                                                         loop body

  direct_nesting                 Static                  True if immediate
                                                         parent-child

  child_invocations_per_parent   Dynamic                 child_invocations /
                                                         parent_invocations

  total_edge_traversals          Dynamic                 Count runtime transitions

  propagation_factor             Derived                 child_total_iterations /
                                                         parent_total_iterations
  ------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 5. Insights Derived from ALG

Based on annotations, we can infer hardware-relevant insights:

## Vectorization Candidates

-   loop_carried_dependency = false
-   innermost loop
-   high arithmetic intensity
-   predictable access pattern

## CPU Parallelization (OpenMP)

-   loop_carried_dependency = false
-   high dynamic_invocations
-   large iteration counts

## GPU-Friendly Loops

-   independent_iterations = true
-   uniform iteration counts
-   high arithmetic intensity
-   minimal branch divergence

## FPGA Pipeline-Amenable

-   bound_static = true
-   low branch_entropy
-   streaming access_pattern
-   small working_set_size

## Memory-Bound Loops

-   low arithmetic_intensity
-   high bytes_read_per_iter

## Reduction Optimization

-   reduction_type ∈ {sum, min, max}
-   associative operation detected

## Kernel Extraction Candidates

-   percentage_runtime high
-   isolated data dependencies

## Offloading Threshold Detection

-   Compare total_time vs data_transfer_cost

