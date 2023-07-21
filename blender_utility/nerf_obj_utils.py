import math
import bpy
import mathutils
import numpy as np
from turbo_nerf.blender_utility.driver_utility import lock_prop_with_driver
from turbo_nerf.blender_utility.obj_type_utility import set_nerf_obj_type
from turbo_nerf.blender_utility.object_utility import add_cube, add_empty
from turbo_nerf.utility.pylib import PyTurboNeRF as tn
from turbo_nerf.constants import (
    CAMERA_CX_ID,
    CAMERA_CY_ID,
    CAMERA_FAR_ID,
    CAMERA_FL_X_ID,
    CAMERA_FL_Y_ID,
    CAMERA_IMAGE_H_ID,
    CAMERA_IMAGE_W_ID,
    CAMERA_INDEX_ID,
    CAMERA_K1_ID,
    CAMERA_K2_ID,
    CAMERA_K3_ID,
    CAMERA_NEAR_ID,
    CAMERA_P1_ID,
    CAMERA_P2_ID,
    CAMERA_SHOW_IMAGE_PLANES_ID,
    NERF_AABB_SIZE_LOG2_ID,
    NERF_ITEM_IDENTIFIER_ID,
    OBJ_TYPE_CAMERAS_CONTAINER,
    OBJ_TYPE_NERF,
    OBJ_TYPE_TRAIN_CAMERA,
)


def add_training_bbox(context, nerf_obj):
    scene = context.scene
    bbox_obj = add_cube("AABB", size=1.0, collection=scene.collection)
    bbox_obj.display_type = "WIRE"
    bbox_obj.parent = nerf_obj

    context.view_layer.objects.active = bbox_obj
    bpy.ops.object.modifier_add(type='WIREFRAME')

    # drivers for linking scale to aabb_size_log2
    [sx, sy, sz] = [fc.driver for fc in bbox_obj.driver_add('scale')]
    for driver in [sx, sy, sz]:
        var_x = driver.variables.new()
        var_x.name = 'aabb_size_log2'
        var_x.targets[0].id = nerf_obj
        var_x.targets[0].data_path = f'["{NERF_AABB_SIZE_LOG2_ID}"]'
        driver.expression = '2**aabb_size_log2'
    
    # lock location to [0,0,0]
    lock_prop_with_driver(bbox_obj, 'location', 0.0)

    # lock rotation to [0,0,0]
    lock_prop_with_driver(bbox_obj, 'rotation_euler', 0.0)

    # lock rotation_mode to XYZ
    lock_prop_with_driver(bbox_obj, 'rotation_mode', 1)


# Render bbox is similar, except it gets its size from tn_nerf_props.crop_{dim}
def add_render_bbox(context, nerf_obj):
    scene = context.scene
    bbox_obj = add_cube("CROP BOX", size=1.0, collection=scene.collection)
    bbox_obj.display_type = "WIRE"
    bbox_obj.parent = nerf_obj

    context.view_layer.objects.active = bbox_obj
    bpy.ops.object.modifier_add(type='WIREFRAME')

    # drivers for linking scale & position to cropping
    locs = [fc.driver for fc in bbox_obj.driver_add('location')]
    scales = [fc.driver for fc in bbox_obj.driver_add('scale')]

    # cycle axes xyz -> zxy - (i - 1) % 3
    for i, dim in enumerate(['x', 'y', 'z']):
        loc = locs[i]
        scale = scales[i]
        
        for driver in [scale, loc]:
            var_min = driver.variables.new()
            var_min.name = f'crop_min'
            var_min.targets[0].id = nerf_obj
            var_min.targets[0].data_path = f'tn_nerf_props.crop_{dim}[0]'

            var_max = driver.variables.new()
            var_max.name = f'crop_max'
            var_max.targets[0].id = nerf_obj
            var_max.targets[0].data_path = f'tn_nerf_props.crop_{dim}[1]'
        
        loc.expression = '(crop_max + crop_min) / 2'
        scale.expression = 'crop_max - crop_min'

    
    # lock other transforms
    lock_prop_with_driver(bbox_obj, 'rotation_euler', 0.0)
    lock_prop_with_driver(bbox_obj, 'rotation_mode', 1)

def create_obj_for_nerf(context: bpy.types.Context, nerf: tn.NeRF) -> bpy.types.Object:

    scene = context.scene
    id = nerf.id

    training_bbox = nerf.training_bbox
    
    nerf_obj = add_cube("NeRF", size=1.0, collection=scene.collection)
    nerf_obj.display_type = "WIRE"

    set_nerf_obj_type(nerf_obj, OBJ_TYPE_NERF)

    nerf_obj[NERF_ITEM_IDENTIFIER_ID] = id
    nerf_obj[NERF_AABB_SIZE_LOG2_ID] = int(round(math.log2(training_bbox.size())))
    aabb_size_log2 = nerf_obj.id_properties_ui(NERF_AABB_SIZE_LOG2_ID)
    aabb_size_log2.update(min=0, max=7)

    # add bounding boxes
    add_render_bbox(context, nerf_obj)

    # only proceed if the nerf has a dataset
    if nerf.dataset is None:
        return nerf_obj

    dataset = nerf.dataset
    cams = dataset.cameras
    add_training_bbox(context, nerf_obj)

    # Add empty for Cameras
    cams_empty = add_empty("CAMERAS", collection=scene.collection)
    cams_empty.parent = nerf_obj
    set_nerf_obj_type(cams_empty, OBJ_TYPE_CAMERAS_CONTAINER)
    
    # Walk through all cameras in dataset, and create a blender camera for each one
    for i, cam in enumerate(cams):
        cam_data = bpy.data.cameras.new(name='Camera')
        cam_obj = bpy.data.objects.new('Camera', cam_data)
        scene.collection.objects.link(cam_obj)
        cam_obj.parent = cams_empty
        
        set_nerf_obj_type(cam_obj, OBJ_TYPE_TRAIN_CAMERA)

        # general properties
        cam_obj[CAMERA_INDEX_ID] = i
        cam_obj[CAMERA_SHOW_IMAGE_PLANES_ID] = cam.show_image_planes

        # image dimensions
        (img_w, img_h) = cam.resolution
        cam_obj[CAMERA_IMAGE_W_ID] = img_w
        cam_obj[CAMERA_IMAGE_H_ID] = img_h

        # near/far planes
        cam_obj[CAMERA_NEAR_ID] = cam.near
        cam_obj[CAMERA_FAR_ID] = cam.far

        # focal length
        (fl_x, fl_y) = cam.focal_length
        cam_obj[CAMERA_FL_X_ID] = fl_x
        cam_obj[CAMERA_FL_Y_ID] = fl_y

        # principal point
        (cx, cy) = cam.principal_point
        cam_obj[CAMERA_CX_ID] = cx
        cam_obj[CAMERA_CY_ID] = cy

        # distortion params
        cam_obj[CAMERA_K1_ID] = cam.dist_params.k1
        cam_obj[CAMERA_K2_ID] = cam.dist_params.k2
        cam_obj[CAMERA_K3_ID] = cam.dist_params.k3
        cam_obj[CAMERA_P1_ID] = cam.dist_params.p1
        cam_obj[CAMERA_P2_ID] = cam.dist_params.p2

        # set transform
        cam_obj.matrix_world = mathutils.Matrix(np.array(cam.transform.to_nerf().to_matrix()))
        
        # set focal length
        fl_x, fl_y = cam.focal_length
        cam_w, cam_h = cam.resolution
        sensor_width = cam_data.sensor_width
        cam_data.lens = sensor_width / cam_w * fl_x
    
    return nerf_obj
