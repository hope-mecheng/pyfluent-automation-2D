# import
import ansys.fluent.core as pyFluent
import os
import time

import io
import sys

# "no_gui", "hidden_gui", or "gui".
gui_Set = "gui"

# The supported values are: 'meshing', 'pure_meshing', 'solver', 'solver_icing', 'solver_aero', 'pre_post'
fluent_mode = pyFluent.FluentMode.MESHING

precision_type = 'double'
processor_amount = 4

cad_file_name = 'ThePart'
cad_file_extension = '.stp'
cad_length_unit = 'mm'

L1 = 30 #mm
L2 = 300 #mm
L = L1+L2
h = 10 #mm

Re_list = [7500]

k_eps = False
k_omg = True

velocity_air = 0.04
density_air = 1000
viscosity_air = 1e-3

iteration_amount = 8000

StuLastNumb = 94

#r = [0.5,1.0,2.0] # mesh quality
r = [1.0]
r.sort() # sorts from lowest to highest

fluent_mode = pyFluent.FluentMode.SOLVER
session = pyFluent.launch_fluent(
    ui_mode = gui_Set, 
    mode = fluent_mode, 
    precision = precision_type, 
    processor_count = processor_amount,
    dimension=pyFluent.Dimension.TWO
)

solver_children = dir(session)
settings = session.settings
#settings_children = dir(settings)
fields = session.fields
#fields_children = dir(fields)

for i in r:
    mesh_quality = i
    session.settings.file.read_mesh(file_name=cad_file_name+f"-mesh_r_{i}.msh.h5")

    time.sleep(1)
    output_buffer = io.StringIO()
    sys.stdout = output_buffer
    
    session.settings.mesh.check()
    
    sys.stdout = sys.__stdout__
    meshcheck_string = output_buffer.getvalue()


    time.sleep(1)

    ## 1. Start logging the Fluent transcript to a temporary file
    #session.transcript.start("temp_mesh_check.log")
    #
    ## 2. Run the mesh check
    #session.settings.mesh.check()
    #
    ## 3. Stop logging so the file saves correctly
    #session.transcript.stop()


    
    # 4. Read the text back into your string variable
    #with open("temp_mesh_check.log", "r") as f:
    #    meshcheck_string = f.read()
    #
    ## (Optional) Print it to verify it captured correctly!
    #print("Captured Mesh Check:\n", meshcheck_string)
    #max_x = None

    for line in meshcheck_string.splitlines():
        if "x-coordinate:" in line:
            # Splits directly at "max (m) =" to isolate the number on the right side
            raw_number = line.split("max (m) =")[1]
            max_x = float(raw_number.strip())
            break

    # Your automated validation check
    if max_x is not None and max_x > L*1e-3 :
        session.settings.mesh.scale(x_scale = 0.001, y_scale = 0.001)
        
    #print(f"Parsed Max X: {max_x}")
    
        
    setup = session.settings.setup
    setup_general = setup.general
    setup_general.set_state({
        'solver': {
            'type': 'pressure-based',
            'two_dim_space': 'planar',
            'velocity_formulation': 'absolute',
            'time': 'steady'
        },
        'operating_conditions': {
            'gravity': {'enable': False,'components': [0, 0]},
            },
    })
    setup_general()
    
    set_model = setup.models
    

    set_model.set_state({
        'multiphase': {'model': 'none'},
        'energy': {'enabled': False},
        'viscous': {
            'model': 'laminar',
            'k_omega_model': 'sst',
            'k_omega': {'k_omega_low_re_correction': False},
            'near_wall_treatment': {'wall_omega_treatment': 'correlation'},
            'transition_module': 'none',
            'options': {
                'curvature_correction': {'enabled': False},
                'corner_flow_correction': {'enabled': False},
                'production_kato_launder_enabled': False,
                'production_limiter': {'enabled': True, 'clip_factor': 10.0}
            },
            'turbulence_expert': {'turb_non_newtonian': False, 'restore_sst_v61': False},
            'user_defined_functions': {'turb_visc': 'none'}
        },
        
        'acoustics': {'model': 'off'},
        
        'radiation': {'model': 'none'},
    
    })

    if k_omg:
        set_model.viscous.set_state({'model': 'k-omega'})
    elif k_eps:
        set_model.viscous.set_state({
            'model': 'k-epsilon',
            'k_epsilon_model': 'standard',
            'near_wall_treatment': {'wall_treatment': 'standard-wall-fn'},
            'options': {'curvature_correction': {'enabled': False},
             'production_kato_launder_enabled': False,
             'production_limiter': {'enabled': False}},
            'turbulence_expert': {'turb_non_newtonian': False},
            'user_defined_functions': {'turb_visc': 'none',
             'tke_prandtl': 'none',
             'tdr_prandtl': 'none'}
        })
    set_model()
    
    materials = setup.materials
    materials.set_state({
        'database': {'database_type': 'fluent-database'},
        'fluid': {'air': {
            'name': 'air',
            'chemical_formula': '',
            'density': {'option': 'value', 'value': 1000},
            'viscosity': {'option': 'value', 'value': 1e-3}},
        },
        'solid': {'aluminum': {
            'name': 'aluminum',
            'chemical_formula': 'al',
            'density': {'option': 'value', 'value': 2719}}
        }
    })
    materials()
    
    
    setup.boundary_conditions.set_zone_type(zone_list=["part1.5"], new_type="pressure-outlet")
    setup.boundary_conditions.set_zone_type(zone_list=["part1.7"], new_type="velocity-inlet")
    setup.boundary_conditions.set_state({
        'wall': {'part1.2': {'name': 'part1.2',
        'momentum': {'wall_motion': 'Stationary Wall',
        'shear_condition': 'No Slip'}},
                 
        'part1.3': {'name': 'part1.3',
        'momentum': {'wall_motion': 'Stationary Wall',
        'shear_condition': 'No Slip'}},
                 
        'part1.4': {'name': 'part1.4',
        'momentum': {'wall_motion': 'Stationary Wall',
        'shear_condition': 'No Slip'}},
                 
        'part1.6': {'name': 'part1.6',
        'momentum': {'wall_motion': 'Stationary Wall',
        'shear_condition': 'No Slip'}},
                 
        'part1.7': {'name': 'part1.7',
        'momentum': {'wall_motion': 'Stationary Wall',
        'shear_condition': 'No Slip'}}},
        
        'pressure_outlet': {
            'part1.5': {
                'name': 'part1.5',
                'momentum': {'backflow_reference_frame': 'Absolute',
                'gauge_pressure': {'option': 'value', 'value': 0},
                'pressure_profile_multiplier': 1.0,
                'backflow_dir_spec_method': 'Normal to Boundary',
                'backflow_pressure_spec': 'Total Pressure',
                'prevent_reverse_flow': False,
                'avg_pressure_spec': False,
                'target_mass_flow_rate': False}
            }
        },
        
        'velocity_inlet': {
            'part1.7': {
                'name': 'part1.7',
                'momentum': {'velocity_specification_method': 'Magnitude, Normal to Boundary',
                'reference_frame': 'Absolute',
                'velocity_magnitude': {'option': 'value', 'value': 0.04},
                'initial_gauge_pressure': {'option': 'value', 'value': 0}},
                'turbulence': {}
            }
        },
    })
    


    setup.boundary_conditions()
    
    solution = session.settings.solution
    solution.methods.set_state({
        'p_v_coupling': {
            'flow_scheme': 'Coupled',
            #'skewness_correction_itr_count': 0,
            'flux_type': 'Rhie-Chow: momentum based',
            'flux_auto_select': True
        },
        'spatial_discretization': {
            'gradient_scheme': 'least-square-cell-based',
            'discretization_scheme': {
                'mom': 'second-order-upwind',
                'pressure': 'second-order'
            }
        },
        'pseudo_time_method': {'formulation': {'coupled_solver': 'global-time-step'}},
        'expert': {
            'implicit_bodyforce_treatment': False,
            'velocity_formulation': 'absolute',
            'physical_velocity_formulation': False,
            'disable_rhie_chow_flux': False,
            'presto_pressure_scheme': False,
            'first_to_second_order_blending': 1.0
        },
        'high_order_term_relaxation': {
            'enable': False,
            'relaxation_factor': 0.25,
            'select_variables': 'flow-variables',
            'type': 'standard'
        },
        'warped_face_gradient_correction': {'enable': False}
    })
    solution.methods()

    solution.controls.set_state({
        'p_v_controls': {},
        'under_relaxation': {
            'body-force': 1.0,
            'density': 1.0,
            'mom': 0.7,
            'pressure': 0.75
        },
    }) 

    solution.controls()
    
    solution.monitor.residual.set_state({
        'equations': {
            'continuity': {
                'monitor': True,
                'check_convergence': True,
                'absolute_criteria': 1e-6
            },
            'epsilon': {
                'monitor': True,
                'check_convergence': True,
                'absolute_criteria': 1e-5
            },
            'k': {
                'monitor': True,
                'check_convergence': True,
                'absolute_criteria': 1e-5
            },
            'x-velocity': {
                'monitor': True,
                'check_convergence': True,
                'absolute_criteria': 1e-6
            },
            'y-velocity': {
                'monitor': True,
                'check_convergence': True,
                'absolute_criteria': 1e-6
            },
            'omega': {
                'monitor': True,
                'check_convergence': True,
                'absolute_criteria': 1e-5
            }
        },
    })
    solution.monitor.residual()

    results = session.settings.results

    surfaces = results.surfaces
    surfaces.line_surface.create()
    surfaces.line_surface.set_state({
        'line-1': {
            'name': 'line-1', 
            'p0': [L1*1e-3+0.02, 0.0, 0.0], 
            'p1': [L1*1e-3+0.02, h*1e-3, 0.0]
        },
        'bottom_wall': {
            'name': 'bottom_wall', 
            'p0': [L1*1e-3, 0.1e-3, 0.0], 
            'p1': [L*1e-3, 0.1e-3, 0.0]
        },
        'top_wall': {
            'name': 'top_wall', 
            'p0': [0, h*1e-3-0.1e-3, 0.0], 
            'p1': [L*1e-3, h*1e-3-0.1e-3, 0.0]
        }
    })

    solution.initialization.set_state({
        'initialization_type': 'hybrid',
        'reference_frame': 'relative',
        'hybrid_init_options': {
            'general_settings': {
                'iter_count': 50,
                'explicit_urf': [1.0, 1.0],
                'initialization_options': {
                    'initial_pressure': False,
                    'external_aero': False,
                    'const_velocity': False
                }
            },
            'turbulent_setting': {'averaged_turbulent_parameters': True}
        },
        'enable_profile_memory_flushing': False
    })

        

    #Custom Setup
    for Re in Re_list:
        velocity_air = Re * viscosity_air / (density_air * h/1000)

        setup.boundary_conditions.set_state({
            'velocity_inlet': {
                'part1.7': {
                    'name': 'part1.7',
                    'momentum': {
                        'velocity_specification_method': 'Magnitude, Normal to Boundary',
                        'reference_frame': 'Absolute',
                        'velocity_magnitude': {'option': 'value', 'value': velocity_air},
                        'initial_gauge_pressure': {'option': 'value', 'value': 0}
                    },
                    'turbulence': {}
                }
            }
        })
        
        solution.initialization()
        solution.initialization.initialize()
        
        solution.run_calculation.iter_count = iteration_amount
        solution.run_calculation()
        
        solution.run_calculation.iterate()

        results.plot.xy_plot.set_state({
            'xy-plot-1': {
                'name': 'xy-plot-1',
                'options': {
                    'node_values': True,
                    'position_on_x_axis': True,
                    'position_on_y_axis': False
                },
                'y_axis_function': 'x-velocity',
                'x_axis_function': 'Direction Vector',
                'x_axis_data': {
                    'option': 'Direction Vector',
                    'x_axis_direction': {
                        'x_component': 1.0, 
                        'y_component': 0.0
                    }
                },
                'y_axis_data': {'option': 'Field Function', 'y_axis_function': 'x-velocity'},
                'surfaces_list': ['line-1'],
                'option': {'node_values': True},
                'plot_direction': {
                    'option': 'direction-vector',
                    'direction_vector': {'x_component': 1.0, 'y_component': 0.0}
                },
                'axes': {
                    'numbers': {
                        'x_format': 'general',
                        'x_axis_precision': 3,
                        'y_format': 'exponential',
                        'y_axis_precision': 2
                    },
                'rules': {
                    'x_axis': {
                        'draw_major_rules': False,
                        'automatic_major_rules': True,
                        'draw_minor_rules': False,
                        'automatic_minor_rules': True
                    },
                    'y_axis': {
                        'draw_major_rules': False,
                        'automatic_major_rules': True,
                        'draw_minor_rules': False,
                        'automatic_minor_rules': True
                    }
                },
                'log_scale': {
                    'x_axis': False, 
                    'y_axis': False
                },
                'auto_scale': {
                    'x_axis': True,
                    'x_axis_min_auto': True,
                    'x_axis_max_auto': True,
                    'y_axis': True,
                    'y_axis_min_auto': True,
                    'y_axis_max_auto': True
                },
                'labels': {'x_axis': '', 'y_axis': ''}
                }
            },
            'xy-plot-2': {
                'name': 'xy-plot-2',
                'options': {
                    'node_values': True,
                    'position_on_x_axis': True,
                    'position_on_y_axis': False
                },
                'y_axis_function': 'x-velocity',
                'x_axis_function': 'Direction Vector',
                'x_axis_data': {
                    'option': 'Direction Vector',
                    'x_axis_direction': {
                        'x_component': 1.0, 
                        'y_component': 0.0
                    }
                },
                'y_axis_data': {'option': 'Field Function', 'y_axis_function': 'x-velocity'},
                'surfaces_list': ['bottom_wall'],
                'option': {'node_values': True},
                'plot_direction': {
                    'option': 'direction-vector',
                    'direction_vector': {'x_component': 1.0, 'y_component': 0.0}
                },
                'axes': {
                    'numbers': {
                        'x_format': 'general',
                        'x_axis_precision': 3,
                        'y_format': 'exponential',
                        'y_axis_precision': 2
                    },
                'rules': {
                    'x_axis': {
                        'draw_major_rules': False,
                        'automatic_major_rules': True,
                        'draw_minor_rules': False,
                        'automatic_minor_rules': True
                    },
                    'y_axis': {
                        'draw_major_rules': False,
                        'automatic_major_rules': True,
                        'draw_minor_rules': False,
                        'automatic_minor_rules': True
                    }
                },
                'log_scale': {
                    'x_axis': False, 
                    'y_axis': False
                },
                'auto_scale': {
                    'x_axis': True,
                    'x_axis_min_auto': True,
                    'x_axis_max_auto': True,
                    'y_axis': True,
                    'y_axis_min_auto': True,
                    'y_axis_max_auto': True
                },
                'labels': {'x_axis': '', 'y_axis': ''}
                }
            },
            'shear-stress-plot': {
                'name': 'shear-stress-plot',
                'options': {
                    'node_values': True,
                    'position_on_x_axis': True,
                    'position_on_y_axis': False
                },
                'y_axis_function': 'x-wall-shear',
                'x_axis_function': 'Direction Vector',
                'x_axis_data': {
                    'option': 'Direction Vector',
                    'x_axis_direction': {
                        'x_component': 1.0, 
                        'y_component': 0.0
                    }
                },
                'y_axis_data': {'option': 'Field Function', 'y_axis_function': 'x-wall-shear'},
                'surfaces_list': ['line-1'],
                'option': {'node_values': True},
                'plot_direction': {
                    'option': 'direction-vector',
                    'direction_vector': {'x_component': 1.0, 'y_component': 0.0}
                },
                'axes': {
                    'numbers': {
                        'x_format': 'float',
                        'x_axis_precision': 3,
                        'y_format': 'float',
                        'y_axis_precision': 2
                    },
                'rules': {
                    'x_axis': {
                        'draw_major_rules': False,
                        'automatic_major_rules': True,
                        'draw_minor_rules': False,
                        'automatic_minor_rules': True
                    },
                    'y_axis': {
                        'draw_major_rules': False,
                        'automatic_major_rules': True,
                        'draw_minor_rules': False,
                        'automatic_minor_rules': True
                    }
                },
                'log_scale': {
                    'x_axis': False, 
                    'y_axis': False
                },
                'auto_scale': {
                    'x_axis': True,
                    'x_axis_min_auto': True,
                    'x_axis_max_auto': True,
                    'y_axis': True,
                    'y_axis_min_auto': True,
                    'y_axis_max_auto': True
                },
                'labels': {'x_axis': '', 'y_axis': ''}
                }
            }
        })

        file_name_base = cad_file_name+f"-II_velocity_profile_Re_{Re}_r_{mesh_quality}"
        for i3 in [".xy",".cas.h5",".dat.h5"]:
            absolute_path = os.path.abspath(file_name_base+i3)
        
            if os.path.exists(absolute_path):
                os.remove(absolute_path)

        
        results.plot.xy_plot['xy-plot-1'].write_to_file(file_name=file_name_base+".xy")

        shear_plot = session.results.plot.xy_plot['shear-stress-plot']

        #shear_plot.y_axis_function = "wall-shear-stress"
        results.plot.xy_plot.set_state({
            'shear-stress-plot': {'surfaces_list': ['part1.4']},
            'xy-plot-2': {'surfaces_list': ['bottom_wall']}
        })  
        #shear_plot.direction_vector.x = 1
        #shear_plot.direction_vector.y = 0

        #shear
        shear_name = f"Wall_Shear_Stress_Re_{Re}_bottom_r_{mesh_quality}_komg.xy"
        absolute_path = os.path.abspath(shear_name)
    
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
            
        shear_plot.write_to_file(file_name=shear_name)

        #vel
        vel_name = f"Wall_xvelocity_Re_{Re}_bottom_r_{mesh_quality}_komg.xy"
        absolute_path = os.path.abspath(vel_name)
    
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
            
        results.plot.xy_plot['xy-plot-2'].write_to_file(file_name=vel_name)

        results.plot.xy_plot.set_state({
            'shear-stress-plot': {'surfaces_list': ['part1.6']},
            'xy-plot-2': {'surfaces_list': ['top_wall']}
        })  
        shear_name = f"Wall_Shear_Stress_Re_{Re}_top_r_{mesh_quality}_komg.xy"

        absolute_path = os.path.abspath(shear_name)
    
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
            
        shear_plot.write_to_file(file_name=shear_name)

        #vel
        vel_name = f"Wall_xvelocity_Re_{Re}_top_r_{mesh_quality}_komg.xy"
        absolute_path = os.path.abspath(vel_name)
    
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
            
        results.plot.xy_plot['xy-plot-2'].write_to_file(file_name=vel_name)


        
        session.settings.file.write_case_data(file_name=file_name_base)

#session.exit()