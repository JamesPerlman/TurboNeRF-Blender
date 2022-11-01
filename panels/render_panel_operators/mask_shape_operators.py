import enum
import bpy
from blender_nerf_tools.constants import (
    MASK_BOX_DIMS_ID,
    MASK_CYLINDER_HEIGHT_ID,
    MASK_CYLINDER_RADIUS_ID,
    MASK_FEATHER_ID,
    MASK_MODE_ID,
    MASK_OPACITY_ID,
    MASK_SPHERE_RADIUS_ID,
    MASK_TYPE_BOX,
    MASK_TYPE_CYLINDER,
    MASK_TYPE_ID,
    MASK_TYPE_SPHERE,
    OBJ_TYPE_ID,
    OBJ_TYPE_MASK_SHAPE,
)

from blender_nerf_tools.blender_utility.object_utility import add_cube, add_cylinder, add_empty, add_sphere, select_object

# TODO: these should be in a different file
def lock_scale_with_drivers(obj):
    drivers = [fc.driver for fc in obj.driver_add('scale')]
    for driver in drivers:
        driver.expression = "1.0"
    
def lock_location_with_drivers(obj):
    drivers = [fc.driver for fc in obj.driver_add('location')]
    for driver in drivers:
        driver.expression = "0.0"

def lock_rotation_with_drivers(obj):
    drivers = [fc.driver for fc in obj.driver_add('rotation_euler')]
    for driver in drivers:
        driver.expression = "0.0"

# Mask utils

def add_mask_specific_properties(mask_base, mask_type):
    if mask_type == MASK_TYPE_BOX:
            mask_base[MASK_BOX_DIMS_ID] = [2.0, 2.0, 2.0]
            props = mask_base.id_properties_ui(MASK_BOX_DIMS_ID)
            props.update(min=-1000.0, max=1000.0, soft_min=-100.0, soft_max=100.0, step=1, precision=3)

    elif mask_type == MASK_TYPE_CYLINDER:
        mask_base[MASK_CYLINDER_RADIUS_ID] = 1.0
        props = mask_base.id_properties_ui(MASK_CYLINDER_RADIUS_ID)
        props.update(min=0.0, max=1000.0, soft_min=0.0, soft_max=100.0, step=1, precision=3)

        mask_base[MASK_CYLINDER_HEIGHT_ID] = 2.0
        props = mask_base.id_properties_ui(MASK_CYLINDER_HEIGHT_ID)
        props.update(min=0.0, max=1000.0, soft_min=0.0, soft_max=100.0, step=1, precision=3)

    elif mask_type == MASK_TYPE_SPHERE:
        mask_base[MASK_SPHERE_RADIUS_ID] = 1.0
        props = mask_base.id_properties_ui(MASK_SPHERE_RADIUS_ID)
        props.update(min=0.0, max=1000.0, soft_min=0.0, soft_max=100.0, step=1, precision=3)
    else:
        raise ValueError(f"Unknown mask type {mask_type}")

def add_mask_box_drivers(mask_base, edge_obj, operator="+"):
    drivers = [fc.driver for fc in edge_obj.driver_add('scale')]
    for idx, driver in enumerate(drivers):
        var_f = driver.variables.new()
        var_f.name = "feather"
        var_f.targets[0].id = mask_base
        var_f.targets[0].data_path = f'["{MASK_FEATHER_ID}"]'

        var_d = driver.variables.new()
        var_d.name = "dim"
        var_d.targets[0].id = mask_base
        var_d.targets[0].data_path = f'["{MASK_BOX_DIMS_ID}"][{idx}]'

        driver.expression = f"max(0.0, (dim / 2.0) {operator} (0.5 * feather))"

def add_mask_cylinder_drivers(mask_base, edge_obj, operator="+"):
    [sx, sy, sz] = [fc.driver for fc in edge_obj.driver_add('scale')]
    for driver in [sx, sy, sz]:
        var_f = driver.variables.new()
        var_f.name = "feather"
        var_f.targets[0].id = mask_base
        var_f.targets[0].data_path = f'["{MASK_FEATHER_ID}"]'

    for driver in [sx, sy]:
        var_r = driver.variables.new()
        var_r.name = "r"
        var_r.targets[0].id = mask_base
        var_r.targets[0].data_path = f'["{MASK_CYLINDER_RADIUS_ID}"]'

    sx.expression = sy.expression = f"max(0.0, r {operator} 0.5 * feather)"
    
    var_h = sz.variables.new()
    var_h.name = "h"
    var_h.targets[0].id = mask_base
    var_h.targets[0].data_path = f'["{MASK_CYLINDER_HEIGHT_ID}"]'

    sz.expression = f"max(0.0, (h / 2.0) {operator} 0.5 * feather)"

def add_mask_sphere_drivers(mask_base, edge_obj, operator="+"):
    drivers = [fc.driver for fc in edge_obj.driver_add('scale')]
    for driver in drivers:
        var_f = driver.variables.new()
        var_f.name = "feather"
        var_f.targets[0].id = mask_base
        var_f.targets[0].data_path = f'["{MASK_FEATHER_ID}"]'

        var_r = driver.variables.new()
        var_r.name = "r"
        var_r.targets[0].id = mask_base
        var_r.targets[0].data_path = f'["{MASK_SPHERE_RADIUS_ID}"]'

        driver.expression = f"max(0.0, r {operator} 0.5 * feather)"

# unused - for nondescript shapes that use scales for feathering instead of individual parameters
def add_mask_edge_scale_drivers(mask_base, visual_obj, operator="+"):
    [sx, sy, sz] = [fc.driver for fc in visual_obj.driver_add('scale')]
    for driver in [sx, sy, sz]:
        var_f = driver.variables.new()
        var_f.name = "feather"
        var_f.targets[0].id = mask_base
        var_f.targets[0].data_path = f'["{MASK_FEATHER_ID}"]'

        var_s = driver.variables.new()
        var_s.name = "base_scale"
        var_s.targets[0].id = mask_base
        var_s.targets[0].data_path = 'scale'
    
    sx.expression = f"1.0 {operator} feather / base_scale[0]"
    sy.expression = f"1.0 {operator} feather / base_scale[1]"
    sz.expression = f"1.0 {operator} feather / base_scale[2]"

MASK_TYPE_TO_PRIMITIVE_CONSTRUCTOR = {
    MASK_TYPE_BOX: add_cube,
    MASK_TYPE_CYLINDER: add_cylinder,
    MASK_TYPE_SPHERE: add_sphere,
}

MASK_TYPE_TO_DRIVER_ADDER = {
    MASK_TYPE_BOX: add_mask_box_drivers,
    MASK_TYPE_CYLINDER: add_mask_cylinder_drivers,
    MASK_TYPE_SPHERE: add_mask_sphere_drivers,
}

MASK_TYPE_TO_NICE_NAME = {
    MASK_TYPE_BOX: "Box",
    MASK_TYPE_CYLINDER: "Cylinder",
    MASK_TYPE_SPHERE: "Sphere",
}

def add_mask_feathering_visualization(mask_base, mask_type):
    if mask_type not in MASK_TYPE_TO_PRIMITIVE_CONSTRUCTOR:
        raise ValueError(f"Unknown mask type {mask_type}")
    
    constructor = MASK_TYPE_TO_PRIMITIVE_CONSTRUCTOR[mask_type]
    driver_adder = MASK_TYPE_TO_DRIVER_ADDER[mask_type]
    nice_name = MASK_TYPE_TO_NICE_NAME[mask_type]

    outer_obj = constructor(name=f"{nice_name} Mask Outer Boundary")
    outer_obj.parent = mask_base
    outer_obj.display_type = "WIRE"
    driver_adder(mask_base, outer_obj, operator="+")
    lock_location_with_drivers(outer_obj)
    lock_rotation_with_drivers(outer_obj)

    
    inner_obj = constructor(name=f"{nice_name} Mask Inner Boundary")
    inner_obj.parent = mask_base
    inner_obj.display_type = "WIRE"
    driver_adder(mask_base, inner_obj, operator="-")
    lock_location_with_drivers(inner_obj)
    lock_rotation_with_drivers(inner_obj)


class BlenderNeRFAddMaskShapeOperator(bpy.types.Operator):
    bl_idname = "blender_nerf.add_mask_shape"
    bl_label = "Add Mask Shape"
    bl_description = "Add a mask shape"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mask_type = context.scene.nerf_render_panel_settings.mask_shape
        mask_base = add_empty(f"{MASK_TYPE_TO_NICE_NAME[mask_type]} Mask Object")
        
        mask_base[OBJ_TYPE_ID] = OBJ_TYPE_MASK_SHAPE
        mask_base[MASK_TYPE_ID] = mask_type
        mask_base[MASK_MODE_ID] = context.scene.nerf_render_panel_settings.mask_mode
        mask_base[MASK_FEATHER_ID] = 0.0
        mask_base[MASK_OPACITY_ID] = 1.0

        add_mask_specific_properties(mask_base, mask_type)
        
        props = mask_base.id_properties_ui(MASK_FEATHER_ID)
        props.update(min=0.0, max=128.0)

        add_mask_feathering_visualization(mask_base, mask_type)
        lock_scale_with_drivers(mask_base)

        select_object(mask_base)

        return {"FINISHED"}
