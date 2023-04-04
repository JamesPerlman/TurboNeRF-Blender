import bpy
import math

from turbo_nerf.blender_utility.driver_utility import force_update_drivers
from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj, get_all_training_cam_objs, get_closest_parent_of_type, get_nerf_obj_type, get_nerf_training_cams, is_nerf_obj_type, is_self_or_some_parent_of_type
from turbo_nerf.constants import (
    CAMERA_FAR_ID,
    CAMERA_INDEX_ID,
    CAMERA_NEAR_ID,
    CAMERA_SHOW_IMAGE_PLANES_ID,
    NERF_AABB_SIZE_LOG2_ID,
    NERF_ITEM_IDENTIFIER_ID,
    OBJ_TYPE_NERF,
    OBJ_TYPE_TRAIN_CAMERA
)
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.render_camera_utils import bl2nerf_cam_train

# general camera prop getter
def get_props_for_cams(nerf_obj, prop_name, default_value):    
    cam_objs = get_nerf_training_cams(nerf_obj, bpy.context)

    if len(cam_objs) == 0:
        return [default_value]
    
    return [o[prop_name] for o in cam_objs]

# kindof a hack for now, need to figure out if there is a cleaner way to do this
# i also don't like that it's just a global method in this file
def update_dataset_cams(nerf_obj):
    nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]
    nerf = NeRFManager.items[nerf_id].nerf
    cam_objs = get_all_training_cam_objs(nerf_obj)

    # todo: only update the cameras that have changed
    nerf.dataset.cameras = [bl2nerf_cam_train(cam_obj) for cam_obj in cam_objs]
    nerf.is_dataset_dirty = True
    

# Custom property group
class NeRFObjectProperties(bpy.types.PropertyGroup):

    # aabb size
    def get_aabb_size(prop_id):
        active_obj = bpy.context.active_object
        nerf_obj = get_closest_parent_of_type(active_obj, OBJ_TYPE_NERF)
        return nerf_obj[NERF_AABB_SIZE_LOG2_ID]

    def set_aabb_size(self, value):
        active_obj = bpy.context.active_object
        nerf_obj = get_closest_parent_of_type(active_obj, OBJ_TYPE_NERF)
        nerf_obj[NERF_AABB_SIZE_LOG2_ID] = value
        force_update_drivers(nerf_obj)

    aabb_options = [
        (f"OPTION{i}", f"{2**i}", f"Set AABB Size to {2**i}")
        for i in range(int(math.log2(128)) + 1)
    ]

    aabb_size: bpy.props.EnumProperty(
        name="AABB Size",
        description="AABB Size",
        items=aabb_options,
        default="OPTION4",
        get=get_aabb_size,
        set=set_aabb_size
    )
    
    # near

    def get_near(prop_id):
        nerf_obj = get_active_nerf_obj(bpy.context)
        return min(get_props_for_cams(nerf_obj, CAMERA_NEAR_ID, 0.0))
    
    def set_near(self, value):
        nerf_obj = get_active_nerf_obj(bpy.context)
        cams = get_nerf_training_cams(nerf_obj, bpy.context)
        for o in cams:
            o[CAMERA_NEAR_ID] = value
            force_update_drivers(o)
        
        update_dataset_cams(nerf_obj)

    near: bpy.props.FloatProperty(
        name="Near Plane",
        description="Near Plane",
        default=0.1,
        min=0.0,
        max=128.0,
        precision=5,
        get=get_near,
        set=set_near,
    )

    # far

    def get_far(prop_id):
        nerf_obj = get_active_nerf_obj(bpy.context)
        return min(get_props_for_cams(nerf_obj, CAMERA_FAR_ID, 128.0))
    
    def set_far(self, value):
        nerf_obj = get_active_nerf_obj(bpy.context)
        cams = get_nerf_training_cams(nerf_obj, bpy.context)
        for o in cams:
            o[CAMERA_FAR_ID] = value
            force_update_drivers(o)

        update_dataset_cams(nerf_obj)

    far: bpy.props.FloatProperty(
        name="Far Plane",
        description="Far Plane",
        default=16.0,
        min=0.0,
        max=128.0,
        precision=5,
        get=get_far,
        set=set_far,
    )

    # show near/far planes

    def get_show_image_planes(prop_id):
        nerf_obj = get_active_nerf_obj(bpy.context)
        return all(get_props_for_cams(nerf_obj, CAMERA_SHOW_IMAGE_PLANES_ID, False))
    
    def set_show_image_planes(self, value):
        nerf_obj = get_active_nerf_obj(bpy.context)
        cams = get_nerf_training_cams(nerf_obj, bpy.context)
        for o in cams:
            o[CAMERA_SHOW_IMAGE_PLANES_ID] = value
            force_update_drivers(o)
        
        update_dataset_cams(nerf_obj)

    show_image_planes: bpy.props.BoolProperty(
        name="Is Visible",
        description="Is Visible",
        default=True,
        get=get_show_image_planes,
        set=set_show_image_planes,
    )

# Custom panel for the dropdown
class NeRFObjectPanel(bpy.types.Panel):
    bl_label = "TurboNeRF Properties"
    bl_idname = "OBJECT_PT_turbo_nerf_object_properties_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    # poll
    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return is_self_or_some_parent_of_type(active_obj, OBJ_TYPE_NERF)
        

    def draw(self, context):
        layout = self.layout
        obj = context.object
        ui_props = obj.tn_nerf_obj_props

        self.draw_dataset_section(context, ui_props)

        self.draw_camera_section(context, ui_props)
    
    def draw_dataset_section(self, context, ui_props):
        layout = self.layout

        row = layout.row()
        row.prop(ui_props, "aabb_size")

    def draw_camera_section(self, context, ui_props):
        selected_cameras = [o for o in context.selected_objects if is_nerf_obj_type(o, OBJ_TYPE_TRAIN_CAMERA)]

        layout = self.layout

        layout.row().separator()

        # single camera
        if len(selected_cameras) == 1:
            cam_obj = selected_cameras[0]
            layout.label(text=f"Editing Camera: {cam_obj.name}")
        elif len(selected_cameras) > 1:
            layout.label(text=f"Editing {len(selected_cameras)} Cameras")
        # all cameras
        else:
            row = layout.row()
            row.label(text="Editing All Cameras")
        
        row = layout.row()
        row.prop(ui_props, "near")

        row = layout.row()
        row.prop(ui_props, "far")

        row = layout.row()
        row.prop(ui_props, "show_image_planes")

        # row = layout.row()
        # row.prop(ui_props, "use_for_training")

        # row = layout.row()
        # row.prop(ui_props, "focal_length")


    # Register the custom property group and panel
    @classmethod
    def register(cls):
        bpy.utils.register_class(NeRFObjectProperties)
        bpy.types.Object.tn_nerf_obj_props = bpy.props.PointerProperty(type=NeRFObjectProperties)


    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(NeRFObjectProperties)
        del bpy.types.Object.tn_nerf_obj_props
