import bpy
from turbo_nerf.blender_utility.driver_utility import lock_prop_with_driver

from turbo_nerf.blender_utility.object_utility import add_cube
from turbo_nerf.constants import (
    NERF_AABB_SIZE_LOG2_ID,
    NERF_CROP_MAX_ID,
    NERF_CROP_MIN_ID
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


# Render bbox is similar, except it gets its size from the NERF_CROP_MIN and NERF_CROP_MAX properties
def add_render_bbox(context, nerf_obj):
    scene = context.scene
    bbox_obj = add_cube("AABB", size=1.0, collection=scene.collection)
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
            var_min.targets[0].data_path = f'["{NERF_CROP_MIN_ID}"][{(i - 1) % 3}]'

            var_max = driver.variables.new()
            var_max.name = f'crop_max'
            var_max.targets[0].id = nerf_obj
            var_max.targets[0].data_path = f'["{NERF_CROP_MAX_ID}"][{(i - 1) % 3}]'
        
        loc.expression = '(crop_max + crop_min) / 2'
        scale.expression = 'crop_max - crop_min'

    
    # lock other transforms
    lock_prop_with_driver(bbox_obj, 'rotation_euler', 0.0)
    lock_prop_with_driver(bbox_obj, 'rotation_mode', 1)
