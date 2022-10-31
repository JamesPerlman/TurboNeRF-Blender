import bpy
from blender_nerf_tools.constants import MASK_FEATHER_ID, MASK_MODE_ADD, MASK_MODE_ID, MASK_OPACITY_ID, MASK_TYPE_BOX, MASK_TYPE_CYLINDER, MASK_TYPE_ID, MASK_TYPE_SPHERE, OBJ_TYPE_ID, OBJ_TYPE_MASK_SHAPE

from blender_nerf_tools.blender_utility.object_utility import add_cube, add_cylinder, add_empty, add_sphere, select_object

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

MASK_TYPE_TO_NICE_NAME = {
    MASK_TYPE_BOX: "Box",
    MASK_TYPE_CYLINDER: "Cylinder",
    MASK_TYPE_SPHERE: "Sphere",
}

def add_mask_primitive_visualization(mask_base, mask_type):
    if mask_type not in MASK_TYPE_TO_PRIMITIVE_CONSTRUCTOR:
        raise ValueError(f"Unknown mask type {mask_type}")
    
    constructor = MASK_TYPE_TO_PRIMITIVE_CONSTRUCTOR[mask_type]
    nice_name = MASK_TYPE_TO_NICE_NAME[mask_type]

    outer_obj = constructor(name=f"{nice_name} Mask Outer Boundary")
    outer_obj.parent = mask_base
    outer_obj.display_type = "WIRE"
    add_mask_edge_scale_drivers(mask_base, outer_obj, operator="+")

    
    inner_obj = constructor(name=f"{nice_name} Mask Inner Boundary")
    inner_obj.parent = mask_base
    inner_obj.display_type = "WIRE"
    add_mask_edge_scale_drivers(mask_base, inner_obj, operator="-")


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
        
        props = mask_base.id_properties_ui(MASK_FEATHER_ID)
        props.update(min=0.0, max=128.0)

        add_mask_primitive_visualization(mask_base, mask_type)

        select_object(mask_base)

        return {"FINISHED"}
