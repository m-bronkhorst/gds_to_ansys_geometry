# gds_to_ansys_geometry
Reads out a .gds file and builds a corresponding 3D geometry in Ansys. Overlapping polygons in the .gds file are stacked vertically to avoid intersections.
This code specifically focuses on planar heterostructure devices with metallic gates deposited on top. However, this can be adjusted. With this code big and complicated layouts can be imported from gds to Ansys and COMSOL automatically, saving time. NOTE: it was written and tested in python 3.8.15.

## Necessary software
The Ansys software used is "Ansys Electronics Dekstop 2022 R2". A license is needed to use this software. For .gds files the free software Klayout editor can be used. The same applies for COMSOL multiphysics when using this code to make a model in COMSOL.

## Overview code
The code contains 6 functions. `open_q3d()` opens Ansys Electronics Desktop in the graphical interface. Similarly, `close_q3d()` closes the Ansys program. All variables, files and dictionaries are given in the function `define_system()`. When changing input(values), this function alone should be adjusted. The function `define_gates()` extracts the polygons from the .gds (containing the metallic gates) and makes and returns the 3D geometries `objects_dict`. These 3D geometries can be build in Ansys with the function `make_gates()`. Function `make_substrate()` makes the (heterostructure) substrate on which the metallic gates are deposited.

In this README I have used the design of a planar heterostructure device with metallic gates as an example.

### `define_system()`
In the function `define_system()` all variables are defined. `GDS_FILE.gds` is the file name of the .gds file, inserting your own .gds file is necessary. For the gates, `# Gates`, values are given that I have used in my own project, these have to be adjusted. In the .gds the object is made out of multiple layers. Each layer has a set of polygons. To find what layers a .gds is made of, open it in Klayout for example. The variables are:

Gates, variables for the metallic gates
- `system.layer_order`: all layers from the .gds, this variable gives the hierarchy in which overlapping gates are stacked. Note that the layer "31" in the .gds is "(31,0)" in the code. In case of gate intersections, the first given layer in the list will be below all other layers and the last layer in the list is on top of all the other layers.
- `system.layer_materials`: material of every layer.
- `system.ver_tolerance`: the vertical space between parts of two gates that are stacked on top of each other. In this space the material is vaccuum.
- `system.hor_tolerance`: when a part of a gate **A** is lifted to be above another gate **B**, the lifted part of **A**, `current_intersection`, is not connected to the rest of **A**. A quick fix is used at line  `current_intersection = current_intersection.buffer(distance=hor_tolerance, join_style=2)` (see the [shapely object.buffer](https://shapely.readthedocs.io/en/stable/manual.html#polygons)). `system.hor_tolerance` gives how much `current_intersection` is enlarged.
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

As an example, the file [Example.gds](Example/Example.gds) is used. In this [figure](Example/Layout_klayout.png) a picture of the gds file is given. Green, red, dark blue, light blue and grey relate to layers (31,0), (21,0), (5,0), (51,0), (3,0) respectively. After running the code, the geometry looks like [this](3D_layout.png) in the Ansys software. Note that the colors have been adjusted in Ansys in light of clarity. In this picture it can be seen how the gates are stacked. Test whether the file paths and variables are correct when running the code for `Example.gds` does not yield similar results.

### `make_gates()`
Makes the geometries of the gates in Ansys and assigns materials to them.

### `make_substrate()`
Makes the substrate. In the example the substrate is made out of layers silicon-germanium, germanium and another layer of silicon-germanium. 

### From Ansys to COMSOL
The 3D model can be extracted from Ansys and imported to COMSOL. Ansys has multiple file types it can be extracted to, note that not all file types support 3D coordinates. COMSOL is capable of importing different file types (see [Comsol site](https://www.comsol.com/fileformats)). I managed to do this succesfully but do not remember the filetype used, I think it was .sab. However some tests should clear that up as it takes very little time. The materials of the model are not inherited to the COMSOL model.

## Possible problems / improvements
Some parts of the code do not work in every situation. Firstly, the code is written and tested in python 3.8.15. The code not working might result from using the code in a different version of python. Secondly, when determining the intersections between the gates in function `define_gates()` it is assumed that the intersections are single Polygons and not Multipolygons. If two gates intersect at two different places this might result in the code not working. Lastly, the raised intersections a enlarged by the `system.hor_tolerance` (see [object.buffer in documentation](https://shapely.readthedocs.io/en/stable/manual.html#polygons)) in order to prevent gates becoming disconnected. In this [figure]() the red lines represent the raised and enlarged intersection. However, this buffer might result in new intersections when gates are very close to each other and it could be that the enlargement is not enough. Always check the model in Ansys to see whether gates have become discontinuous or have started overlapping. This method could be improved by going through the point of an intersection and moving the outer points along the gates, see this [figure](). Here the red points are the coordinates of the insersection and instead of dilating the intersection, the instersection keep the same width and the length is increased, like the red arrows.

Finally, this method relies on Ansys to create a 3D model. However Ansys requires licensing and therefore it might be nice to find a way of making and showing the 3D models without Ansys.
