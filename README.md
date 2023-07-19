# gds_to_ansys_geometry
Reads out a .gds file and builds a corresponding 3D geometry in Ansys. Overlapping polygons in the .gds file are stacked vertically to avoid intersections.
This code specifically focuses on planar heterostructure devices with metallic gates deposited on top. However, this can be adjusted.

## Necessary software
The Ansys software used is "Ansys Electronics Dekstop 2022 R2". A license is needed to use this software. For .gds files the free software Klayout editor can be used.

## Overview code
The code contains 6 functions. `open_q3d()` opens Ansys Electronics Desktop in the graphical interface. Similarly, `close_q3d()` closes the Ansys program. All variables, files and dictionaries are given in the function `define_system()`. When changing input(values), this function alone should be adjusted. The function `define_gates()` extracts the polygons from the .gds (containing the metallic gates) and makes and returns the 3D geometries `objects_dict`. These 3D geometries can be build in Ansys with the function `make_gates()`. Function `make_substrate()` makes the (heterostructure) substrate on which the metallic gates are deposited.

In this README I have used the design of a planar heterostructure device with metallic gates as an example.

### `define_system()`
In the function `define_system()` all variables are defined. `GDS_FILE.gds` is the file name of the .gds file. For the gates now values are given that I have used in my own project, these have to be adjusted. In the .gds the object is made out of multiple layers. Each layer has a set of polygons, to find what layers a .gds is made of, open it in Klayout:
![Main window of Klayout, the layers are given on the right](https://www.klayout.de/doc-qt5/manual/main_window.png)

### `define_gates()`

### `make_gates()`

### `make_substrate()`
