# Abaqus Modeling Scripts

This is a collection of scripts for performing various tasks related to [Abaqus](https://www.3ds.com/products/simulia/abaqus) Finite Element Modeling (FEM).

- most of the `abq_*` programs operate on Abaqus input or output files directly
- `abq_modeling_helpers` is a collection of routines meant to be imported into a live Abaqus CAE interactive modeling session
- the `plot_*` scripts operate on `*.rpt` files output in Abaqus, and use [the Generic Mapping Tools (GMT)](https://www.generic-mapping-tools.org/) to generate plots

Designed for Python 2.7, although only minor changes (e.g. `print()` statements) needed for 3.x conversion.

Copyright ⓒ David Blair, 2024.
