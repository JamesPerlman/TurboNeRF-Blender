import bpy
import math

from turbo_nerf.blender_utility.driver_utility import force_update_drivers

from turbo_nerf.blender_utility.obj_type_utility import (
    get_all_training_cam_objs,
    get_closest_parent_of_type,
    get_nerf_training_cams,
    is_nerf_obj_type,
    is_self_or_some_parent_of_type
)

from turbo_nerf.constants import (
    CAMERA_FAR_ID,
    CAMERA_NEAR_ID,
    CAMERA_SHOW_IMAGE_PLANES_ID,
    NERF_AABB_SIZE_LOG2_ID,
    OBJ_TYPE_NERF,
    OBJ_TYPE_TRAIN_CAMERA
)
from turbo_nerf.utility.math import clamp
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn
from turbo_nerf.utility.render_camera_utils import bl2nerf_cam_train

# helper methods
# kinda dirty to put these in the global scope for this file

def get_props_for_cams(nerf_obj, prop_name, default_value):    
    cam_objs = get_nerf_training_cams(nerf_obj, bpy.context)

    if len(cam_objs) == 0:
        return [default_value]
    
    return [o[prop_name] for o in cam_objs]

# updates the dataset cameras for a nerf object
def set_props_for_cams(nerf_obj, nerf):
    cam_objs = get_all_training_cam_objs(nerf_obj)

    # todo: only update the cameras that have changed
    nerf.dataset.cameras = [bl2nerf_cam_train(cam_obj, relative_to=nerf_obj) for cam_obj in cam_objs]
    nerf.is_dataset_dirty = True

# Custom property group
# self.id_data below is shorthand for the active object, and more robust than bpy.context.active_object
class NeRFObjectProperties(bpy.types.PropertyGroup):

    # aabb size
    def get_aabb_size(self: bpy.types.PropertyGroup):
        nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
        return nerf_obj[NERF_AABB_SIZE_LOG2_ID]

    def set_aabb_size(self: bpy.types.PropertyGroup, value):
        active_obj = self.id_data
        nerf_obj = get_closest_parent_of_type(active_obj, OBJ_TYPE_NERF)
        nerf_obj[NERF_AABB_SIZE_LOG2_ID] = value

        # TODO: update nerf's training bbox on the CUDA side

        # update the nerf's render bbox
        size = 2 ** value
        nerf = NeRFManager.get_nerf_for_obj(nerf_obj)
        nerf.render_bbox = tn.BoundingBox(size)

        self.crop_x = (-size / 2, size / 2)
        self.crop_y = (-size / 2, size / 2)
        self.crop_z = (-size / 2, size / 2)
        
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

    def get_near(self):
        nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
        return min(get_props_for_cams(nerf_obj, CAMERA_NEAR_ID, 0.0))
    
    def set_near(self, value):
        nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
        cams = get_nerf_training_cams(nerf_obj, bpy.context)
        for o in cams:
            o[CAMERA_NEAR_ID] = value
        
        set_props_for_cams(nerf_obj, NeRFManager.get_nerf_for_obj(nerf_obj))

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

    def get_far(self):
        nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
        return min(get_props_for_cams(nerf_obj, CAMERA_FAR_ID, 128.0))
    
    def set_far(self, value):
        nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
        cams = get_nerf_training_cams(nerf_obj, bpy.context)
        for o in cams:
            o[CAMERA_FAR_ID] = value

        set_props_for_cams(nerf_obj, NeRFManager.get_nerf_for_obj(nerf_obj))

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

    def get_show_image_planes(self):
        nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
        return all(get_props_for_cams(nerf_obj, CAMERA_SHOW_IMAGE_PLANES_ID, False))
    
    def set_show_image_planes(self, value):
        nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)

        # it is not great to use bpy.context here, but it is the only way.
        cams = get_nerf_training_cams(nerf_obj, bpy.context)
        for o in cams:
            o[CAMERA_SHOW_IMAGE_PLANES_ID] = value
        
        set_props_for_cams(nerf_obj, NeRFManager.get_nerf_for_obj(nerf_obj))

    show_image_planes: bpy.props.BoolProperty(
        name="Is Visible",
        description="Is Visible",
        default=True,
        get=get_show_image_planes,
        set=set_show_image_planes,
    )

    # cropping (render bbox)

    def get_crop(dim: str):
        if dim not in ("x", "y", "z"):
            raise ValueError(f"Invalid dimension {dim} for crop")
        
        def crop_getter(self):
            nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
            nerf = NeRFManager.get_nerf_for_obj(nerf_obj)
            min_dim = getattr(nerf.render_bbox, f"min_{dim}")
            max_dim = getattr(nerf.render_bbox, f"max_{dim}")
            return (min_dim, max_dim)

        return crop_getter
    
    def set_crop(dim):
        if dim not in ("x", "y", "z"):
            raise ValueError(f"Invalid dimension {dim} for crop")
        
        def crop_setter(self, value):
            nerf_obj = get_closest_parent_of_type(self.id_data, OBJ_TYPE_NERF)
            nerf = NeRFManager.get_nerf_for_obj(nerf_obj)

            # defensively clamp the values to the training bbox
            # also ensure that min <= max

            tbbox_min = getattr(nerf.training_bbox, f"min_{dim}")
            tbbox_max = getattr(nerf.training_bbox, f"max_{dim}")

            rbbox_min = getattr(nerf.render_bbox, f"min_{dim}")
            rbbox_max = getattr(nerf.render_bbox, f"max_{dim}")

            new_min = clamp(value[0], tbbox_min, rbbox_max)
            new_max = clamp(value[1], rbbox_min, tbbox_max)

            new_bbox = nerf.render_bbox
            setattr(new_bbox, f"min_{dim}", new_min)
            setattr(new_bbox, f"max_{dim}", new_max)

            # this sets the props on the CUDA side and sets is_dirty to True so the new updates get rendered
            nerf.render_bbox = new_bbox

        return crop_setter
    
    # we need to switch the axes here from xyz to zxy
    
    crop_x: bpy.props.FloatVectorProperty(
        name="Crop X",
        description="Crop X",
        min=-128.0,
        max=128.0,
        size=2,
        step=0.01,
        precision=5,
        get=get_crop("z"),
        set=set_crop("z"),
    )

    crop_y: bpy.props.FloatVectorProperty(
        name="Crop Y",
        description="Crop Y",
        min=-128.0,
        max=128.0,
        size=2,
        step=0.01,
        precision=5,
        get=get_crop("x"),
        set=set_crop("x"),
    )

    crop_z: bpy.props.FloatVectorProperty(
        name="Crop Z",
        description="Crop Z",
        min=-128.0,
        max=128.0,
        size=2,
        step=0.01,
        precision=5,
        get=get_crop("y"),
        set=set_crop("y"),
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
        obj = context.object
        ui_props = obj.tn_nerf_props

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

        # only NeRF object properties beyond this point

        if not is_nerf_obj_type(context.object, OBJ_TYPE_NERF):
            return

        # crop section (only for NeRF objects)
        
        row = layout.row()
        row.label(text="Crop")

        row = layout.row()
        row.prop(ui_props, "crop_x")

        row = layout.row()
        row.prop(ui_props, "crop_y")

        row = layout.row()
        row.prop(ui_props, "crop_z")

    # Register the custom property group and panel
    @classmethod
    def register(cls):
        bpy.utils.register_class(NeRFObjectProperties)
        bpy.types.Object.tn_nerf_props = bpy.props.PointerProperty(type=NeRFObjectProperties)


    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(NeRFObjectProperties)
        del bpy.types.Object.tn_nerf_props
