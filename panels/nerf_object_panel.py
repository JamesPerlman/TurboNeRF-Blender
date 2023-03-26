import bpy
import math

from turbo_nerf.blender_utility.obj_type_utility import is_nerf_obj_type
from turbo_nerf.constants import (
    NERF_AABB_SIZE_LOG2_ID,
    OBJ_TYPE_NERF
)

# Custom property group
class NeRFObjectProperties(bpy.types.PropertyGroup):

    def get_aabb_size(prop_id):
        raw_size_log2 = bpy.context.active_object[NERF_AABB_SIZE_LOG2_ID]

        # round to nearest power of 2
        return raw_size_log2

    def set_aabb_size(self, value):
        nerf_obj = bpy.context.active_object
        
        aabb_size = 2**int(value)
        nerf_obj[NERF_AABB_SIZE_LOG2_ID] = value

    aabb_options = [
        (f"OPTION{i}", f"{2**i}", f"Set AABB Size to {2**i}")
        for i in range(int(math.log2(128)) + 1)
    ]

    aabb_size: bpy.props.EnumProperty(
        name="AABB Size",
        description="Custom Dropdown Enum",
        items=aabb_options,
        default="OPTION4",
        get=get_aabb_size,
        set=set_aabb_size
    )

# Custom panel for the dropdown
class NeRFObjectPanel(bpy.types.Panel):
    bl_label = "Custom Dropdown"
    bl_idname = "OBJECT_PT_nerf_object_properties_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    # poll
    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return is_nerf_obj_type(active_obj, OBJ_TYPE_NERF)
        

    def draw(self, context):
        layout = self.layout
        obj = context.object
        ui_props = obj.tn_nerf_obj_props

        row = layout.row()
        row.prop(ui_props, "aabb_size")


    # Register the custom property group and panel
    @classmethod
    def register(cls):
        bpy.utils.register_class(NeRFObjectProperties)
        bpy.types.Object.tn_nerf_obj_props = bpy.props.PointerProperty(type=NeRFObjectProperties)

    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(NeRFObjectProperties)
        del bpy.types.Object.tn_nerf_obj_props
