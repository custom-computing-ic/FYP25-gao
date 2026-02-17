# QUBO CPU Solver

This project implements a CPU-based local search solver for **QUBO
(Quadratic Unconstrained Binary Optimization)** problems.

The solver uses: - Bit-packed binary variables - Incremental
delta-energy updates - Random restarts - Greedy local search

------------------------------------------------------------------------

## What is QUBO?

A **QUBO** problem is defined as:

E(x) = xᵀ Q x

Where: - `x` is a vector of binary variables (0 or 1) - `Q` is an N×N
symmetric matrix of weights

The goal is to find the binary vector `x` that minimizes the energy
function.

QUBO problems appear in: - Combinatorial optimization - Graph problems
(MaxCut, MIS, etc.) - Machine learning - Quantum annealing
formulations - Hardware acceleration research

------------------------------------------------------------------------

## How the Solver Works

The solver performs:

1.  **Randomization phase**
    -   Generates pseudo-random flips of variables.
2.  **Greedy local search**
    -   Repeatedly flips the variable that most reduces energy (ΔE \<
        0).
    -   Stops when no improving flip exists (local minimum).
3.  **Multiple restarts (STEP iterations)**
    -   Keeps the best solution found.

Energy is maintained incrementally using a delta-energy array for
efficiency.

------------------------------------------------------------------------

## Input File Format (CSV)

The CSV file must have:

Line 1: N

Lines 2..N+1: Upper triangular matrix values (including diagonal), comma
separated.

Example (N=3):

    3
    1,2,3
    4,5
    6

The matrix is assumed symmetric. The code mirrors the upper triangle
into the lower.

------------------------------------------------------------------------

## Build Instructions

Simply run:

    make

This produces:

    cpu_qubo

Requirements: - C++11 compatible compiler - Linux / macOS environment

------------------------------------------------------------------------

## Running the Solver

Basic usage:

    ./cpu_qubo input.csv

Optional STEP parameter:

    ./cpu_qubo input.csv 5000

Where:

-   `input.csv` = QUBO matrix file
-   `STEP` = number of random restarts (default: 1000)

------------------------------------------------------------------------

## Increasing Problem Size

Problem size is controlled by:

### 1️⃣ Matrix size (N)

Change the first line of the CSV file to a larger N and provide a
corresponding NxN matrix.

Larger N increases: - Memory usage (O(N²)) - Runtime (local search is
roughly O(N²) per restart)

### 2️⃣ STEP (number of restarts)

Higher STEP: - Improves solution quality (more exploration) - Increases
runtime linearly

Example:

    ./cpu_qubo large_matrix.csv 20000

------------------------------------------------------------------------

## Performance Notes

Time complexity roughly:

-   Energy computation: O(N²)
-   apply_flip: O(N)
-   search_cpu: O(N²) worst case
-   Total runtime: O(STEP × N²)

The solver is CPU-only and single-threaded.

