# import
import ansys.fluent.core as pyFluent
import os
import time

# "no_gui", "hidden_gui", or "gui".
gui_Set = "gui"

# The supported values are: 'meshing', 'pure_meshing', 'solver', 'solver_icing', 'solver_aero', 'pre_post'
fluent_mode = pyFluent.FluentMode.MESHING

precision_type = 'double'
processor_amount = 4

cad_file_name = 'ThePart'
cad_file_extension = '.stp'
cad_length_unit = 'mm'

L1 = 30
L2 = 300
h = 40

StuLastNumb = 94

local_sizing_config = {
    'edgesize_1': {
        'zone_list': ["part1.6","part1.2","part1.4"],
        'boi_size': (L1+L2)/(400+StuLastNumb),
        'boi_assign_using': 'Size',
        'zone_or_label': 'zone'
    },
    'edgesize_2': {
        'zone_list': ["part1.5"],
        'boi_size': h,
        'boi_assign_using': 'Interval',
        'zone_or_label': 'zone'
    },
    'edgesize_3': {
        'zone_list': ["part1.7","part1.3"],
        'boi_size': h/2,
        'boi_assign_using': 'Interval',
        'zone_or_label': 'zone'
    }
}

r = [0.5,1.0,2.0] # mesh quality
r.sort(reverse=True) # sorts from highest to lowest

# Functions
def child_config(two_dim_mesh, child_name, zone_list, boi_size, boi_assign_using = 'Interval', zone_or_label = 'zone'): 
    found_child = None
    for attr in dir(two_dim_mesh):
        if attr.startswith('add_local_sizing_2d_child_'):
            child_obj = getattr(two_dim_mesh, attr)
            if child_obj.boi_control_name.get_state() == str(child_name):
                found_child = child_obj
                break
    
    if found_child is not None:
        #add_local_sizing = getattr(two_dim_mesh,'add_local_sizing_2d_'+str(child_name))
        #add_local_sizing.revert() - add this to main code
        
        #add_local_sizing = two_dim_mesh.add_local_sizing_2d_child_1
        #add_local_sizing.boi_control_name = str(child_name)
        found_child.boi_execution = 'Edge Size'
        found_child.assign_size_using = boi_assign_using
        found_child.boi_size = boi_size 
        found_child.numberof_layers = int(boi_size)
        found_child.boi_zoneor_label = zone_or_label
        found_child.draw_size_control = True
        found_child.edge_zone_list = zone_list
        found_child.execute()
    else:
        add_local_sizing = two_dim_mesh.add_local_sizing_2d
        add_local_sizing.add_child = "yes"
        add_local_sizing.boi_control_name = str(child_name)
        add_local_sizing.boi_execution = 'Edge Size'
        add_local_sizing.assign_size_using = boi_assign_using
        add_local_sizing.boi_size = boi_size 
        add_local_sizing.numberof_layers = int(boi_size)
        add_local_sizing.boi_zoneor_label = zone_or_label
        add_local_sizing.draw_size_control = True
        add_local_sizing.edge_zone_list = zone_list #["part1.6","part1.2","part1.4"]
        add_local_sizing.add_child_and_update(defer_update=False)

#Meshing session
session = pyFluent.launch_fluent(ui_mode = gui_Set, mode = fluent_mode, precision = precision_type, processor_count = processor_amount)

two_dim_mesh = session.two_dimensional_meshing()

time.sleep(5)
load_cad = two_dim_mesh.load_cad_geometry_2d
load_cad.file_name = cad_file_name + cad_file_extension
load_cad.length_unit = cad_length_unit
load_cad.refaceting.refacet = False
load_cad()

update_cell = two_dim_mesh.update_regions_2d
update_cell()

update_bnd = two_dim_mesh.update_boundaries_2d
update_bnd.selection_type = "zone"
update_bnd()

global_sizing = two_dim_mesh.define_global_sizing_2d
global_sizing.curvature_normal_angle = 180
global_sizing.max_size = 100.0
global_sizing.min_size = 0.01
global_sizing.size_functions = "Curvature"
global_sizing.mesher = "MultiZone"
global_sizing()

for i in r:
    if i != r[0]:
        add_local_sizing = two_dim_mesh.add_local_sizing_2d
        add_local_sizing.revert()

    for i2 in range(0,len(local_sizing_config)):
        struct_child_name, stc_cf = list(local_sizing_config.items())[i2]
        if stc_cf['boi_assign_using'] == "Interval":
            sel_boi_size = stc_cf['boi_size']*i
        else:
            sel_boi_size = stc_cf['boi_size']/i
        child_config(two_dim_mesh,struct_child_name,stc_cf['zone_list'],sel_boi_size,stc_cf['boi_assign_using'],stc_cf['zone_or_label'])

    add_boundary_layers = two_dim_mesh.add_2d_boundary_layers
    add_boundary_layers()

    generate_surface_mesh = two_dim_mesh.generate_initial_surface_mesh
    generate_surface_mesh.generate_quads = True
    mesh_preferences = two_dim_mesh.generate_initial_surface_mesh.surface_2d_preferences
    mesh_preferences.show_advanced_options = True
    mesh_preferences.merge_edge_zones_based_on_labels = "no"
    mesh_preferences.merge_face_zones_based_on_labels = "no"
    generate_surface_mesh()

    export = two_dim_mesh.write_2d_mesh
    file_name_base = cad_file_name+f"-mesh_r_{i}.msh.h5"
    absolute_path = os.path.abspath(file_name_base)

    if os.path.exists(absolute_path):
        os.remove(absolute_path)
        
    export.file_name = absolute_path
    
    session.tui.file.confirm_overwrite("no")
    export()
    time.sleep(3)

session.exit()