# gds_to_ansys_geometry
Reads out a .gds file and builds a corresponding 3D geometry in Ansys. Overlapping polygons in the .gds file are stacked vertically to avoid intersections.
This code specifically focuses on planar heterostructure devices with metallic gates deposited on top. However, this can be adjusted.

## Necessary software
The Ansys software used is "Ansys Electronics Dekstop 2022 R2". A license is needed to use this software. For .gds files the free software Klayout editor can be used.

## Overview code
The code contains 6 functions. `open_q3d()` opens Ansys Electronics Desktop in the graphical interface. Similarly, `close_q3d()` closes the Ansys program. All variables, files and dictionaries are given in the function `define_system()`. When changing input(values), this function alone should be adjusted. The function `define_gates()` extracts the polygons from the .gds (containing the metallic gates) and makes and returns the 3D geometries `objects_dict`. These 3D geometries can be build in Ansys with the function `make_gates()`. Function `make_substrate()` makes the (heterostructure) substrate on which the metallic gates are deposited.

In this README I have used the design of a planar heterostructure device with metallic gates as an example.

### `define_system()`
In the function `define_system()` all variables are defined. `GDS_FILE.gds` is the file name of the .gds file, inserting your own .gds file is necessary. For the gates, `# Gates`, values are given that I have used in my own project, these have to be adjusted. In the .gds the object is made out of multiple layers. Each layer has a set of polygons. To find what layers a .gds is made of, open it in Klayout for example. The variables are:

Gates, variables for the metallic gates
- `system.layer_order`: all layers from the .gds, this variable gives the hierarchy in which overlapping gates are stacked. Note that the layer "31" in the .gds is "(31,0)" in the code. In case of gate intersections, the first given layer in the list will be below all other layers and the last layer in the list is on top of all the other layers.
- `system.layer_materials`: material of every layer.
- `system.ver_tolerance`: the vertical space between parts of two gates that are stacked on top of each other. In this space the material is vaccuum.
- `system.hor_tolerance`: when a part of a gate **A** is lifted to be above another gate **B**, the lifted part of **A**, `current_intersection`, is not connected to the rest of **A**. A quick fix is used at line  `current_intersection = current_intersection.buffer(distance=hor_tolerance, join_style=2)` (see the shapely Polygon.buffer at https://shapely.readthedocs.io/en/stable/reference/shapely.Polygon.html). `system.hor_tolerance` gives how much `current_intersection` is enlarged.
- `system.zpos`: offsets of layers in the z-direction.

Substrate, the heterostructure that is below the metal gates
- `system.list_substrates`: List of names used in Ansys for the different substrate layers
- `system.coords_substrate`: coordinates of the substrate layers
- `system.z_coords`: z-coordinates of the substrate layers
- `system.heights`: heights of the substrate layers
- `system.materials`: materials of the substrate latyers

### `define_gates()`
This function extracts the polygon coordinates from the .gds file and returns a corresponding 3D geometry, `objects_dict`. NOTE: this function assumes only gates are included in the .gds file. The function prohibits the intersection of gates from different layers and will vertically stack them according to the order of `system.layer_order`. `objects_dict` also contains the height and the materials of the gates. For each layer the gates are separated as well, making it possible to select individual gates in Ansys.

Order of the function:
- Import data from .gds file
- Storing polygons per layer
- separating the gates in each layer
- Determine the intersecting polygons for all layers
- Raise intersections above upper gate
- Store everything in `objects_dict`

As an example, the file [Example.gds](Example.gds) is used.

### `make_gates()`

### `make_substrate()`

### From Ansys to COMSOL

## Possible problems / improvements
- shapely buffer
