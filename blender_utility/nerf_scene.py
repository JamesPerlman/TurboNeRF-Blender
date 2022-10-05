__reload_order_index__ = -2

import bpy
from blender_nerf_tools.blender_utility.driver_utility import force_update_drivers
from blender_nerf_tools.blender_utility.logging_utility import log_report
from blender_nerf_tools.blender_utility.obj_type_utility import get_object_type
from blender_nerf_tools.blender_utility.object_utility import (
    add_collection,
    add_cube,
    add_empty,
    get_collection,
    get_object
)
from blender_nerf_tools.constants import (
    AABB_BOX_ID,
    AABB_IS_CUBE_DEFAULT,
    AABB_IS_CUBE_ID,
    AABB_MAX_DEFAULT,
    AABB_MAX_ID,
    AABB_MIN_DEFAULT,
    AABB_MIN_ID,
    CAMERA_FAR_ID,
    CAMERA_NEAR_ID,
    CAMERA_USE_FOR_TRAINING_ID,
    GLOBAL_TRANSFORM_ID,
    MAIN_COLLECTION_ID,
    NERF_PROPS_ID,
    OBJ_TYPE_TRAIN_CAMERA,
    POINT_CLOUD_NAME_DEFAULT,
    POINT_CLOUD_POINT_SIZE_ID,
    TIME_DEFAULT,
    TIME_ID,
    TRAINING_STEPS_DEFAULT,
    TRAINING_STEPS_ID,
)
from blender_nerf_tools.photogrammetry_importer.opengl.draw_manager import DrawManager

class NeRFScene:
    @classmethod
    def main_collection(cls):
        collection = get_collection(MAIN_COLLECTION_ID)
        return collection
    
    @classmethod
    def create_main_collection(cls):
        collection = cls.main_collection()
        if collection is None:
            collection = add_collection(MAIN_COLLECTION_ID)
        return collection

    # GLOBAL TRANSFORM

    @classmethod
    def global_transform(cls):
        return get_object(GLOBAL_TRANSFORM_ID)
    
    @classmethod
    def create_global_transform(cls):
        collection = cls.main_collection()
        obj = cls.global_transform()
        if obj is None:
            obj = add_empty(GLOBAL_TRANSFORM_ID, collection)
        if not obj.name in collection.objects:
            cls.main_collection().objects.link(obj)
        return obj
    
    # SETUP

    @classmethod
    def setup(cls):
        cls.create_main_collection()
        cls.create_nerf_props()
        cls.create_aabb_box()
        cls.create_global_transform()

    @classmethod
    def is_setup(cls):
        return (
            cls.main_collection() is not None
            and cls.aabb_box() is not None
            and cls.global_transform() is not None
            and cls.nerf_props() is not None
        )

    # AABB BOX

    @classmethod
    def create_aabb_box(cls):
        collection = cls.main_collection()
        obj = cls.aabb_box()
        if obj is None:
            obj = add_cube(AABB_BOX_ID, collection)
            bpy.context.view_layer.objects.active = obj
            obj.display_type = 'BOUNDS'
            bpy.ops.object.modifier_add(type='WIREFRAME')
            
            # Set up custom AABB min prop
            obj[AABB_MIN_ID] = AABB_MIN_DEFAULT
            prop = obj.id_properties_ui(AABB_MIN_ID)
            prop.update(precision=5)

            # Set up custom AABB max prop
            obj[AABB_MAX_ID] = AABB_MAX_DEFAULT
            prop = obj.id_properties_ui(AABB_MAX_ID)
            prop.update(precision=5)

            # Set up custom AABB "is cubical" prop
            obj[AABB_IS_CUBE_ID] = AABB_IS_CUBE_DEFAULT

            # Helper method for adding min/max vars to a driver
            def add_min_max_vars(driver: bpy.types.Driver, axis: int):
                axis_name = ["x", "y", "z"][axis]
                
                vmin = driver.variables.new()
                vmin.name = f"{axis_name}_min"
                vmin.targets[0].id = obj
                vmin.targets[0].data_path = f"[\"{AABB_MIN_ID}\"][{axis}]"

                vmax = driver.variables.new()
                vmax.name = f"{axis_name}_max"
                vmax.targets[0].id = obj
                vmax.targets[0].data_path = f"[\"{AABB_MAX_ID}\"][{axis}]"

            # Set up drivers for location
            [px, py, pz] = [fc.driver for fc in obj.driver_add("location")]

            add_min_max_vars(px, 0)
            px.expression = "0.5 * (x_min + x_max)"

            add_min_max_vars(py, 1)
            py.expression = "0.5 * (y_min + y_max)"

            add_min_max_vars(pz, 2)
            pz.expression = "0.5 * (z_min + z_max)"
            
            # Set up drivers for scale
            [sx, sy, sz] = [fc.driver for fc in obj.driver_add("scale")]

            add_min_max_vars(sx, 0)
            sx.expression = "x_max - x_min"

            add_min_max_vars(sy, 1)
            sy.expression = "y_max - y_min"

            add_min_max_vars(sz, 2)
            sz.expression = "z_max - z_min"
        
        if not obj.name in collection.objects:
            collection.objects.link(obj)
        
        return obj

    @classmethod
    def aabb_box(cls):
        return get_object(AABB_BOX_ID)
    
    @classmethod
    def get_aabb_min(cls):
        return cls.aabb_box()[AABB_MIN_ID]
    
    @classmethod
    def set_aabb_min(cls, value):
        aabb_max = cls.get_aabb_max()
        if cls.get_is_aabb_cubical():
            aabb_size_half = 0.5 * (aabb_max[0] - value[0])
            aabb_center = cls.get_aabb_center()
            value = [aabb_center[i] - aabb_size_half for i in range(3)]
        safe_min = [min(value[i], aabb_max[i]) for i in range(3)]
        cls.aabb_box()[AABB_MIN_ID] = safe_min
        cls.update_aabb_box_drivers()

    @classmethod
    def get_aabb_max(cls):
        return cls.aabb_box()[AABB_MAX_ID]
    
    @classmethod
    def set_aabb_max(cls, value):
        aabb_min = cls.get_aabb_min()
        if cls.get_is_aabb_cubical():
            aabb_size_half = 0.5 * (value[0] - aabb_min[0])
            aabb_center = cls.get_aabb_center()
            value = [aabb_center[i] + aabb_size_half for i in range(3)]
        safe_max = [max(value[i], aabb_min[i]) for i in range(3)]
        cls.aabb_box()[AABB_MAX_ID] = safe_max
        cls.update_aabb_box_drivers()

    @classmethod
    def get_aabb_size(cls):
        max = cls.get_aabb_max()
        min = cls.get_aabb_min()
        return [max[i] - min[i] for i in range(3)]
    
    @classmethod
    def set_aabb_size(cls, value):
        center = cls.get_aabb_center()
        if cls.get_is_aabb_cubical():
            value = [value[0], value[0], value[0]]
        
        safe_size = [max(0, value[i]) for i in range(3)]

        aabb_box = cls.aabb_box()
        aabb_box[AABB_MAX_ID] = [center[i] + 0.5 * safe_size[i] for i in range(3)]
        aabb_box[AABB_MIN_ID] = [center[i] - 0.5 * safe_size[i] for i in range(3)]
        cls.update_aabb_box_drivers()
    
    @classmethod
    def get_aabb_center(cls):
        max = cls.get_aabb_max()
        min = cls.get_aabb_min()
        return [0.5 * (max[i] + min[i]) for i in range(3)]
    
    @classmethod
    def set_aabb_center(cls, value):
        size = cls.get_aabb_size()
        
        aabb_box = cls.aabb_box()
        aabb_box[AABB_MAX_ID] = [value[i] + 0.5 * size[i] for i in range(3)]
        aabb_box[AABB_MIN_ID] = [value[i] - 0.5 * size[i] for i in range(3)]
        cls.update_aabb_box_drivers()
    
    @classmethod
    def get_is_aabb_cubical(cls) -> bool:
        return cls.aabb_box()[AABB_IS_CUBE_ID]
    
    @classmethod
    def set_is_aabb_cubical(cls, value: bool):
        if value is True:
            new_size = cls.get_aabb_size()[0]
            cls.set_aabb_size([new_size, new_size, new_size])
        cls.aabb_box()[AABB_IS_CUBE_ID] = value
    
    @classmethod
    def update_aabb_box_drivers(cls):
        obj = cls.aabb_box()
        force_update_drivers(obj)
    
    # NERF PROPERTIES

    @classmethod
    def create_nerf_props(cls):
        collection = cls.main_collection()
        obj = cls.nerf_props()
        
        if obj == None:
            obj = add_empty(NERF_PROPS_ID, collection)
            
            obj[TRAINING_STEPS_ID] = TRAINING_STEPS_DEFAULT

            obj[TIME_ID] = TIME_DEFAULT
            prop_mgr = obj.id_properties_ui(TIME_ID)
            prop_mgr.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
        
        if not obj.name in collection.objects:
            collection.objects.link(obj)
    
    @classmethod
    def nerf_props(cls):
        return get_object(NERF_PROPS_ID)

    @classmethod
    def get_nerf_prop(cls, prop_id):
        if prop_id in cls.nerf_props():
            return cls.nerf_props()[prop_id]
        else:
            return None
    
    @classmethod
    def set_training_steps(cls, value: int):
        cls.nerf_props()[TRAINING_STEPS_ID] = value
    
    @classmethod
    def get_training_steps(cls):
        return cls.nerf_props()[TRAINING_STEPS_ID]
    
    @classmethod
    def get_time(cls):
        return cls.get_nerf_prop(TIME_ID)
    
    # CAMERA SELECTION

    @classmethod
    def is_nerf_camera(cls, obj):
        return obj.type == 'CAMERA' and get_object_type(obj) == OBJ_TYPE_TRAIN_CAMERA

    @classmethod
    def get_selected_cameras(cls):
        return [obj for obj in bpy.context.selected_objects if cls.is_nerf_camera(obj)]
    
    @classmethod
    def get_all_cameras(cls):
        return [obj for obj in bpy.data.objects if cls.is_nerf_camera(obj)]
    
    @classmethod
    def select_all_cameras(cls):
        for camera in cls.get_all_cameras():
            camera.select_set(True)
            cls.update_image_plane_visibility_for_camera(camera)
    
    @classmethod
    def deselect_all_cameras(cls):
        # bpy.ops.object.select_all(action='DESELECT')
        for camera in cls.get_all_cameras():
            camera.select_set(False)
            cls.update_image_plane_visibility_for_camera(camera)

    @classmethod
    def set_selected_camera(cls, camera, change_view = False):
        camera.select_set(True)
        bpy.context.view_layer.objects.active = camera
        if change_view:
            cls.set_view_from_camera(camera)

    @classmethod
    def select_camera_with_offset(cls, offset):
        selected_cameras = cls.get_selected_cameras()
        NeRFScene.deselect_all_cameras()
        if len(selected_cameras) == 1:
            current_camera = selected_cameras[0]
            all_cameras = cls.get_all_cameras()
            current_camera_index = all_cameras.index(current_camera)
            target_camera = all_cameras[(current_camera_index + offset) % len(all_cameras)]
            cls.set_selected_camera(target_camera)

    @classmethod
    def select_previous_camera(cls):
        cls.select_camera_with_offset(-1)
    
    @classmethod
    def select_next_camera(cls):
        cls.select_camera_with_offset(1)
    
    @classmethod
    def select_first_camera(cls):
        selected_cameras = cls.get_selected_cameras()
        NeRFScene.deselect_all_cameras()
        if len(selected_cameras) > 1:
            cls.set_selected_camera(selected_cameras[0])
        else:
            cls.set_selected_camera(cls.get_all_cameras()[0])

    @classmethod
    def select_last_camera(cls):
        selected_cameras = cls.get_selected_cameras()
        NeRFScene.deselect_all_cameras()
        if len(selected_cameras) > 1:
            cls.set_selected_camera(selected_cameras[-1])
        else:
            cls.set_selected_camera(cls.get_all_cameras()[-1])

    @classmethod
    def select_cameras_inside_radius(cls, radius):
        cls.deselect_all_cameras()
        for camera in cls.get_all_cameras():
            dist_to_cursor = (camera.matrix_world.translation - bpy.context.scene.cursor.location).length
            if dist_to_cursor <= radius:
                camera.select_set(True)
                cls.update_image_plane_visibility_for_camera(camera)
    
    @classmethod
    def select_cameras_outside_radius(cls, radius):
        cls.deselect_all_cameras()
        for camera in cls.get_all_cameras():
            dist_to_cursor = (camera.matrix_world.translation - bpy.context.scene.cursor.location).length
            if dist_to_cursor > radius:
                camera.select_set(True)
                cls.update_image_plane_visibility_for_camera(camera)

    @classmethod
    def set_active_camera(cls, camera):
        bpy.context.scene.camera = camera

    @classmethod
    def set_view_from_camera(cls, camera):
        bpy.context.scene.camera = camera
        # thank you https://blender.stackexchange.com/a/30645/141797
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                break
    
    # CAMERA PROPERTIES

    # near

    @classmethod
    def set_camera_near(cls, camera, value, update_drivers = True):
        camera[CAMERA_NEAR_ID] = value

        # update image plane drivers
        if update_drivers:
            force_update_drivers(camera)
    
    @classmethod
    def get_camera_near(cls, camera):
        return camera[CAMERA_NEAR_ID]
    
    @classmethod
    def set_near_for_selected_cameras(cls, value):
        for camera in cls.get_selected_cameras():
            cls.set_camera_near(camera, value)
    
    @classmethod
    def get_near_for_selected_cameras(cls):
        selected_cameras = cls.get_selected_cameras()
        if len(selected_cameras) > 0:
            return cls.get_camera_near(selected_cameras[0])
        return 0.0
    
    # far
    
    @classmethod
    def set_camera_far(cls, camera, value, update_drivers = True):
        camera[CAMERA_FAR_ID] = value

        # update image plane drivers
        if update_drivers:
            force_update_drivers(camera)

    @classmethod
    def get_camera_far(cls, camera):
        return camera[CAMERA_FAR_ID]
    
    @classmethod
    def set_far_for_selected_cameras(cls, value):
        for camera in cls.get_selected_cameras():
            cls.set_camera_far(camera, value)
    
    @classmethod
    def get_far_for_selected_cameras(cls):
        selected_cameras = cls.get_selected_cameras()
        if len(selected_cameras) > 0:
            return cls.get_camera_far(selected_cameras[0])
        return 0.0

    # training enabled

    @classmethod
    def get_training_cameras(cls):
        return [cam for cam in cls.get_all_cameras() if cam[CAMERA_USE_FOR_TRAINING_ID] == True]

    @classmethod
    def get_use_selected_cameras_for_training(cls):
        selected_cameras = cls.get_selected_cameras()
        if len(selected_cameras) > 0:
            return selected_cameras[0][CAMERA_USE_FOR_TRAINING_ID]
        return False
    
    @classmethod
    def set_use_selected_cameras_for_training(cls, value, show_non_training_cameras):
        for camera in cls.get_selected_cameras():
            camera[CAMERA_USE_FOR_TRAINING_ID] = value
            hide_camera = value == False and show_non_training_cameras == False
            camera.hide_set(hide_camera)
            for child in camera.children:
                child.hide_set(hide_camera)
                
    # visibility

    @classmethod
    def update_cameras_visibility(cls, show_non_training_cameras):
        for camera in cls.get_all_cameras():
            is_training_camera = camera[CAMERA_USE_FOR_TRAINING_ID] == False
            hide_non_training_cameras = show_non_training_cameras == False
            camera.hide_set(is_training_camera and hide_non_training_cameras)
    
    # CAMERA IMAGE PLANE VISIBILITY

    @classmethod
    def update_image_plane_visibility_for_camera(cls, camera, force_visible = None):
        for child in camera.children:
            is_visible: bool
            if force_visible is not None:
                is_visible = force_visible
            else:
                is_visible =  camera.select_get()
            child.hide_set(not is_visible)
    
    @classmethod
    def update_image_plane_visibility_for_all_cameras(cls, force_visible = None):
        """ Updates the image plane visibility for all selected cameras. """
        for camera in cls.get_all_cameras():
            cls.update_image_plane_visibility_for_camera(camera, force_visible)

    # POINT CLOUD
    @classmethod
    def point_cloud(cls):
        return get_object(POINT_CLOUD_NAME_DEFAULT)

    @classmethod
    def get_viz_point_size(cls):
        point_cloud = cls.point_cloud()

        if point_cloud is None:
            return 0
        
        return cls.point_cloud()[POINT_CLOUD_POINT_SIZE_ID]

    @classmethod
    def set_viz_point_size(cls, value):
        point_cloud = cls.point_cloud()
        point_cloud[POINT_CLOUD_POINT_SIZE_ID] = value
        draw_manager = DrawManager.get_singleton()
        draw_back_handler = draw_manager.get_draw_callback_handler(
            point_cloud
        )
        draw_back_handler.set_point_size(value)
    
