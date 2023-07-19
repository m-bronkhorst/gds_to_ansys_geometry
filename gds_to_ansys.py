# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18

@author: m-bronkhorst
"""
#%%
#### NOTE: THE DATA IS STORED IN A LIST-BASED WAY. NOT REALLY A BOTTLENECK OF SPEED, BUT IT IS UGLY. FOR A VERSION 2, REMAKE IT SUCH THAT IT IS SAVED AS A NUMPY ARRAY (WITHIN DICTIONARIES)
#### NOTE: define_system() contains all variables. When changing .gds files and directories, only this function needs to be changed
import os
import gdspy
import shapely as sh
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.strtree import STRtree
from shapely.ops import unary_union
import pyaedt
import numpy as np

def open_q3d():
    # Opens up Ansys with a Graphical Interface
    # If you don't want it graphical, set the string to True
    ### Make sure to be connected with the licence server (e.g. with eduVPN)
    
    graphical_bool_str = 'False'
    non_graphical = os.getenv("PYAEDT_NON_GRAPHICAL", graphical_bool_str).lower() in ("true", "1", "t")
    # Choses random project name
    q = pyaedt.Q3d(projectname=str(pyaedt.generate_unique_project_name()),
                   specified_version="2022.2",
                   non_graphical=non_graphical,
                   new_desktop_session=True)
    
    return q
    
def close_q3d(q):
    q.release_desktop(close_projects=True, close_desktop=True)

def define_system():
    ## NOTE: THE CURRENT VALUES IN define_system() HAVE TO BE ADJUSTED FOR EVERY .gds FILE
    # Making an object to define global system characteristics
    class NewClass(object): pass
    system = NewClass()

    # Files
    current_dir = os.path.dirname(os.path.realpath(__file__))
    system.current_dir = os.path.dirname(os.path.realpath(__file__))
    system.file_path = current_dir+"\\Example.gds" # of gds file

    # Gates
    system.layer_order = [(3, 0), (5, 0), (51, 0), (31, 0), (21, 0)] # Layers in the gds file, open the file in Klayout to see the layers
    system.layer_heights = {3:20e-3, 5:20e-3, 51:20e-3, 31:30e-3, 21:40e-3} # in um
    system.layer_materials = {3:"copper", 5:"copper", 51:"copper", 31:"copper", 21:"copper"} # Materials of all layers
    system.ver_tolerance = 5e-3 # Vertical space between gates stacked vertically
    system.hor_tolerance = 3e-3 # How much a raised intersection of gates will be blown up to try to keep gate continuous
    system.zpos = {3:0.0, 5:0.0, 51:0.0, 31:0.0, 21:0.0} # Offset in z-direction of all layers
    
    # Substrate
    system.list_substrates = ['SiGe1', 'Ge', 'SiGe2']
    system.coords_substrate = [[-0.40000,-1.00000],[-1.20000,-0.40000],[-1.2000,0.40000],[-1.20000,0.40000],[-0.40000,1.00000],[0.40000,1.0000],[1.20000,0.40000],[1.20000,-0.40000],[0.40000,-1.00000],[-0.40000,-1.00000]]
    system.z_coords = {'SiGe1': 0.0, 'Ge':-57*1e-3, 'SiGe2': -67*1e-3} 
    system.heights = {'SiGe1':-57*1e-3, 'Ge':-10*1e-3, 'SiGe2':-100*1e-3}
    system.materials = {'SiGe1':'Si2Ge8', 'Ge':'germanium', 'SiGe2':'Si2Ge8'}

    return system

system = define_system()


def define_gates():
    print("Extract data from gds file")
    # Importing data from the gds file
    file_path = system.file_path
    lib = gdspy.GdsLibrary(infile=file_path)
    main_cell = lib.top_level()[0]
    print('Unit, precision = ', gdspy.get_gds_units(file_path))

    # Extracting the layer numbers and polygons from the .gds
    pol_dict = main_cell.get_polygons(by_spec=True)
    layers = main_cell.get_layers()

    # Some properties of the gates
    order_layers = system.layer_order
    heights = system.layer_heights
    zpos = system.zpos
    ver_tolerance = system.ver_tolerance
    hor_tolerance = system.hor_tolerance
    materials = system.layer_materials

    # Storing all polygons in one list per layer
    polygon_set = {}
    for key in pol_dict:
        polygons = [Polygon(np.vstack((p, p[0]))) for p in pol_dict[key]]
        polygon_set[key] = polygons

    # Storing the coordinates of the polygons of all the layers
    objects_dict = {}

    # Separate each gate in each layer
    cleaned_pol_dict = {}
    cleaned_polygon_set = {}
    for key in pol_dict:
        union_in_layer = unary_union(polygon_set[key])
        if union_in_layer.geom_type == 'MultiPolygon':
            polygons_in_layer = list(union_in_layer.geoms)
            cleaned_pol_dict[key] = [sh.get_coordinates(p) for p in polygons_in_layer]
            cleaned_polygon_set[key] = polygons_in_layer

    pol_dict = cleaned_pol_dict
    polygon_set = cleaned_polygon_set

    # Making STRtree of all layers for a faster comparison of polygons between layers
    str_set = {key: STRtree(polygon_set[key]) for key in polygon_set}

    # Storing the properties and geometries
    objects_dict = {}
    for key, polygons in pol_dict.items():
        objects_dict[f'layer_{key[0]}'] = {}

        for j, polygon in enumerate(polygons):
            temp_dict = {}
            temp_dict['height'] = heights[key[0]]
            temp_dict['material'] = materials[key[0]]

            # Adding the z-coordinates
            zpos_array = zpos[key[0]] * np.ones((polygon.shape[0], 1))
            temp_polygons = np.hstack((polygon, zpos_array))
            temp_dict[f'geometry_lay_{key[0]}_pol_{j}'] = temp_polygons
            merge_list = [f'geometry_lay_{key[0]}_pol_{j}']
            temp_dict['merge_list'] = merge_list
            objects_dict[f'layer_{key[0]}'][f'gate_{j}'] = temp_dict

    print("Vertically stacking intersecting gates")
    # Vertically stacking overlapping polygons on top of each other
    # Hierarchy of which layer should be below which is order_layers
    layers_beneath = []
    for main_layer in order_layers:
        polygon_overlap = {}
        # Find which polygons overlap
        for i, layer_beneath in enumerate(layers_beneath): # Excluding above main_layers
            indices_overlap = str_set[main_layer].query(polygon_set[layer_beneath], predicate='overlaps').T
            for overlap in indices_overlap: # overlap[1], overlap[0] are the indeces of main_layer and index of layer beneath 
                idx_lower_polygon = overlap[0]
                idx_higher_polygon = overlap[1]
                if not (idx_higher_polygon in polygon_overlap.keys()):
                    polygon_overlap[idx_higher_polygon] = []
                layer_poly_idx = (layer_beneath, idx_lower_polygon)
                polygon_overlap[idx_higher_polygon].append(layer_poly_idx)

        # Find intersection geometries
        for polygon_idx, overlaps in polygon_overlap.items():
            current_difference = polygon_set[main_layer][polygon_idx]
            for overlap_layer, overlap_polygon_idx in overlaps:
                # Does not take into account the intersections being a multipolygon
                # Find the geometries of the overlapping polygons and the non-overlapping polygons
                current_intersection = sh.intersection(polygon_set[main_layer][polygon_idx], polygon_set[overlap_layer][overlap_polygon_idx])
                # Raise and broaden the intersection NOTE: "buffer" can result in discontinuous gates
                current_intersection = current_intersection.buffer(distance=hor_tolerance, join_style=2)
                current_difference = sh.difference(current_difference, current_intersection)

                # Add z-values to intersection
                z_intersection = (objects_dict[f'layer_{overlap_layer[0]}'][f'gate_{overlap_polygon_idx}']['height'] + ver_tolerance + zpos[main_layer[0]]) * np.ones((len(np.asarray(current_intersection.exterior.coords)), 1))
                temp_intersection = np.hstack((np.asarray(current_intersection.exterior.coords), z_intersection))
                # Change the object geometry to the intersection
                num_geom = len(objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}']['merge_list'])
                new_pol_name = f'geometry_lay_{main_layer[0]}_pol_{polygon_idx}subpol_{num_geom}'
                objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}'][new_pol_name] = temp_intersection
                objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}']['merge_list'].append(new_pol_name)

            # Give z-values to the difference geoemtry. The difference should be added as another geometry of 
            # the object. For a MultiPolygon every operations has to be applied per Polygon
            num_geom = len(objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}']['merge_list'])
            if current_difference.geom_type == 'MultiPolygon':
                for k, geom in enumerate(current_difference.geoms):
                    temp_dif = np.asarray(geom.exterior.coords)
                    z_difference = zpos[main_layer[0]] * np.ones((temp_dif.shape[0], 1))
                    new_pol_name = f'geometry_lay_{main_layer[0]}_pol_{polygon_idx}subpol_{num_geom + k}'
                    objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}'][new_pol_name] = np.hstack((temp_dif, z_difference))
                    objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}']['merge_list'].append(new_pol_name)
            else:
                temp_dif = np.asarray(current_difference.exterior.coords)
                z_difference = zpos[main_layer[0]] * np.ones((temp_dif.shape[0], 1))
                new_pol_name = f'geometry_lay_{main_layer[0]}_pol_{polygon_idx}subpol_{num_geom}'
                objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}'][new_pol_name] = np.hstack((temp_dif, z_difference))
                objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}']['merge_list'].append(new_pol_name)

            old_pol_name = f'geometry_lay_{main_layer[0]}_pol_{polygon_idx}'
            del objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}'][old_pol_name]
            objects_dict[f'layer_{main_layer[0]}'][f'gate_{polygon_idx}']['merge_list'].remove(old_pol_name)

        layers_beneath.append(main_layer)

    lib = None
    main_cell = None
    pol_dict = None
    temp_dict = None

    print("Data updated")
    return objects_dict

def make_gates(q,objects_dict):
    all_gate_names = []
    for layer in objects_dict:
        print("Layer ", layer)
        for gate in objects_dict[layer]:
            merge_list = objects_dict[layer][gate]["merge_list"]
            for geometry_name in merge_list:
                q.modeler.create_polyline(objects_dict[layer][gate][geometry_name],name=geometry_name)
                q.modeler.cover_lines(geometry_name)
                q.modeler.sweep_along_vector(geometry_name,[0,0,objects_dict[layer][gate]["height"]])
            q.modeler.unite(merge_list)
            q.modeler[merge_list[0]].name = layer+'_'+gate
            all_gate_names.append(layer+gate)

            q.assign_material(layer+'_'+gate,objects_dict[layer][gate]["material"])

    
def make_substrate(q): 
    # Characteristics of the substrate
    list_substrates = system.list_substrates
    coords_substrate = system.coords_substrate
    z_coords = system.z_coords
    heights = system.heights
    materials = system.materials


    # Making every substrate with the correct position, height and material
    for substrate_layer in list_substrates:
        num_coords = len(coords_substrate)
        z = z_coords[substrate_layer]*np.ones((num_coords, 1))
        coords = np.hstack((coords_substrate,z))
        q.modeler.create_polyline(coords, name=substrate_layer, matname=materials[substrate_layer])
        q.modeler.cover_lines(substrate_layer)
        q.modeler.sweep_along_vector(substrate_layer,[0,0,heights[substrate_layer]])

    heterstructure_colors = {"SiGe1":(120,60,230),"Ge":(230,60,120),"SiGe2":(250,80,80)}

    
    for key in heterstructure_colors.keys():
        # q.modeler[key].color = heterstructure_colors[key]
        q.modeler[key].transparency = 0.6

#%%
q = open_q3d()
# ### MAKE SURE TO MANUALLY MAKE um THE DEFAULT LENGTH UNIT!!!!
#%%
gate_model = define_gates()
gate_model.keys()
#%%
make_gates(q, gate_model)

#%%
make_substrate(q)
