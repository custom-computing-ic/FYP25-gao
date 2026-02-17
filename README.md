# Metaprogramming for Heterogenous Compute

## Frameworks

- **Artisan**: Used to analyse and transform C++ programs. Installation instructions can be found [here](https://github.com/custom-computing-ic/artisan).
- **Heterograph**: Used to build graphs with metadata, such as ALG (see below). This library is installed with the Artisan conda environment (see instructions above). Heterograph documentation can be found [here](https://custom-computing-ic.github.io/heterograph/).

## Analysis

### Annotated Loop Graph

The [Annotated Loop Graph (ALG)](ALG.md) is a structural abstraction of a program
that captures its **repetition topology** and the hardware-relevant
properties of repetitive computation.

An ALG does not encode full program semantics. Instead, it represents:

-   Where repetition occurs (loops)
-   How repetition propagates (nesting and calls)
-   What workload characteristics are associated with each loop
-   How repetition scales dynamically

## Benchmarks

- [Qubo](apps/qubo/)


