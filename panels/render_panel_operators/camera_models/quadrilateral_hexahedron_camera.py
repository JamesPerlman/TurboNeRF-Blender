import mathutils
import numpy as np

from blender_nerf_tools.blender_utility.object_utility import add_empty
from blender_nerf_tools.constants import (
    OBJ_TYPE_ID,
    OBJ_TYPE_RENDER_CAMERA,
    RENDER_CAM_NEAR_ID,
    RENDER_CAM_QUAD_HEX_BACK_SENSOR_SIZE_ID,
    RENDER_CAM_QUAD_HEX_FRONT_SENSOR_SIZE_ID,
    RENDER_CAM_QUAD_HEX_SENSOR_LENGTH_ID,
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON,
)

# drivers

def add_front_sensor_size_driver_var(driver, cam_base):
    var_fs = driver.variables.new()
    var_fs.name = "fs"
    var_fs.targets[0].id = cam_base
    var_fs.targets[0].data_path = f'["{RENDER_CAM_QUAD_HEX_FRONT_SENSOR_SIZE_ID}"]'

def add_back_sensor_size_driver_var(driver, cam_base):
    var_bs = driver.variables.new()
    var_bs.name = "bs"
    var_bs.targets[0].id = cam_base
    var_bs.targets[0].data_path = f'["{RENDER_CAM_QUAD_HEX_BACK_SENSOR_SIZE_ID}"]'

def add_sensor_length_driver_var(driver, cam_base):
    var_sl = driver.variables.new()
    var_sl.name = "sl"
    var_sl.targets[0].id = cam_base
    var_sl.targets[0].data_path = f'["{RENDER_CAM_QUAD_HEX_SENSOR_LENGTH_ID}"]'

def add_front_node_location_drivers(cam_base, cam_node):
    [lx, ly, lz] = [fc.driver for fc in cam_node.driver_add('location')]
    for driver in [lx, ly]:
        add_front_sensor_size_driver_var(driver, cam_base)
        add_sensor_length_driver_var(driver, cam_base)
    
    add_sensor_length_driver_var(lz, cam_base)

    return [lx, ly, lz]

def add_back_node_location_drivers(cam_base, cam_node):
    [lx, ly, lz] = [fc.driver for fc in cam_node.driver_add('location')]
    for driver in [lx, ly]:
        add_back_sensor_size_driver_var(driver, cam_base)
        add_sensor_length_driver_var(driver, cam_base)
    
    add_sensor_length_driver_var(lz, cam_base)

    return [lx, ly, lz]

def add_sample_node_location_drivers(cam_base, cam_node):
    [lx, ly, lz] = [fc.driver for fc in cam_node.driver_add('location')]
    for driver in [lx, ly]:
        add_front_sensor_size_driver_var(driver, cam_base)
        add_back_sensor_size_driver_var(driver, cam_base)
        add_sensor_length_driver_var(driver, cam_base)

    add_sensor_length_driver_var(lz, cam_base)

    return [lx, ly, lz]

def add_sample_node_quaternion_drivers(cam_base, cam_node):
    drivers = [fc.driver for fc in cam_node.driver_add('rotation_quaternion')]
    for driver in drivers:
        add_front_sensor_size_driver_var(driver, cam_base)
        add_back_sensor_size_driver_var(driver, cam_base)
        add_sensor_length_driver_var(driver, cam_base)

    return drivers

# utils
# z- is forward in blender
def get_quadrilateral_hexahedron_camera_node_quaternion_rotation(front_sensor_size, back_sensor_size, sensor_length, cx, cy):
    front_x = front_sensor_size[0] * cx
    front_y = front_sensor_size[1] * cy
    front_z = -sensor_length / 2.0
    back_x = back_sensor_size[0] * cx
    back_y = back_sensor_size[1] * cy
    back_z = sensor_length / 2.0

    front_p = mathutils.Vector([front_x, front_y, front_z])
    back_p = mathutils.Vector([back_x, back_y, back_z])

    # get the direction vector
    dir_vec = (front_p - back_p).normalized()

    # convert to quaternion
    return dir_vec.to_track_quat('Z', 'X')

# function that adds the camera to the scene

def add_quadrilateral_hexahedron_camera(name='Quadrilateral Hexahedron Camera', collection=None):

    cam_base = add_empty(name, collection=collection, type='ARROWS')
    cam_base[OBJ_TYPE_ID] = OBJ_TYPE_RENDER_CAMERA
    cam_base[RENDER_CAM_TYPE_ID] = RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON

    # add custom properties
    cam_base[RENDER_CAM_NEAR_ID] = 0.0
    prop = cam_base.id_properties_ui(RENDER_CAM_NEAR_ID)
    prop.update(min=0.0, max=100.0)

    cam_base[RENDER_CAM_QUAD_HEX_FRONT_SENSOR_SIZE_ID] = [1.0, 1.0]
    prop = cam_base.id_properties_ui(RENDER_CAM_QUAD_HEX_FRONT_SENSOR_SIZE_ID)
    prop.update(min=-100, max=100)

    cam_base[RENDER_CAM_QUAD_HEX_BACK_SENSOR_SIZE_ID] = [1.0, 1.0]
    prop = cam_base.id_properties_ui(RENDER_CAM_QUAD_HEX_BACK_SENSOR_SIZE_ID)
    prop.update(min=-100, max=100)

    cam_base[RENDER_CAM_QUAD_HEX_SENSOR_LENGTH_ID] = 1.0

    # add faces and vertices
    front_face = add_empty('Front Face', collection=collection, type='PLAIN_AXES')
    front_face.parent = cam_base
    front_nodes = {
        'tl': add_empty('Front Top Left', collection=collection, type='PLAIN_AXES'),
        'tr': add_empty('Front Top Right', collection=collection, type='PLAIN_AXES'),
        'bl': add_empty('Front Bottom Left', collection=collection, type='PLAIN_AXES'),
        'br': add_empty('Front Bottom Right', collection=collection, type='PLAIN_AXES'),
    }
    for node in front_nodes.values():
        node.parent = front_face
    
    back_face = add_empty('Back Face', collection=collection, type='PLAIN_AXES')
    back_face.parent = cam_base
    back_nodes = {
        'tl': add_empty('Back Top Left', collection=collection, type='PLAIN_AXES'),
        'tr': add_empty('Back Top Right', collection=collection, type='PLAIN_AXES'),
        'bl': add_empty('Back Bottom Left', collection=collection, type='PLAIN_AXES'),
        'br': add_empty('Back Bottom Right', collection=collection, type='PLAIN_AXES'),
    }
    for node in back_nodes.values():
        node.parent = back_face
    
    # add drivers to front nodes
    [lx, ly, lz] = add_front_node_location_drivers(cam_base, front_nodes['tl'])
    lx.expression = "fs[0] * -0.5"
    ly.expression = "fs[1] * 0.5"
    lz.expression = "sl * -0.5"

    [lx, ly, lz] = add_front_node_location_drivers(cam_base, front_nodes['tr'])
    lx.expression = "fs[0] * 0.5"
    ly.expression = "fs[1] * 0.5"
    lz.expression = "sl * -0.5"

    [lx, ly, lz] = add_front_node_location_drivers(cam_base, front_nodes['bl'])
    lx.expression = "fs[0] * -0.5"
    ly.expression = "fs[1] * -0.5"
    lz.expression = "sl * -0.5"

    [lx, ly, lz] = add_front_node_location_drivers(cam_base, front_nodes['br'])
    lx.expression = "fs[0] * 0.5"
    ly.expression = "fs[1] * -0.5"
    lz.expression = "sl * -0.5"

    # add drivers to back nodes
    [lx, ly, lz] = add_back_node_location_drivers(cam_base, back_nodes['tl'])
    lx.expression = "bs[0] * -0.5"
    ly.expression = "bs[1] * 0.5"
    lz.expression = "sl * 0.5"

    [lx, ly, lz] = add_back_node_location_drivers(cam_base, back_nodes['tr'])
    lx.expression = "bs[0] * 0.5"
    ly.expression = "bs[1] * 0.5"
    lz.expression = "sl * 0.5"

    [lx, ly, lz] = add_back_node_location_drivers(cam_base, back_nodes['bl'])
    lx.expression = "bs[0] * -0.5"
    ly.expression = "bs[1] * -0.5"
    lz.expression = "sl * 0.5"

    [lx, ly, lz] = add_back_node_location_drivers(cam_base, back_nodes['br'])
    lx.expression = "bs[0] * 0.5"
    ly.expression = "bs[1] * -0.5"
    lz.expression = "sl * 0.5"


    # create sample nodes with arrows (on back face pointing to front face)
    
    rx, ry = 10, 10

    coords = (np.stack(np.mgrid[:rx, :ry], -1) / [rx - 1, ry - 1] - [0.5, 0.5])
    coords = coords.reshape(-1, coords.shape[-1])
    
    sample_nodes = add_empty('Sample Nodes', collection=collection, type='PLAIN_AXES')
    sample_nodes.parent = cam_base

    for coord in coords:
        [cx, cy] = coord

        node = add_empty('Sample Node', collection=collection, type='SINGLE_ARROW')
        node.rotation_mode = 'QUATERNION'
        node.parent = sample_nodes
        
        [lx, ly, lz] = add_sample_node_location_drivers(cam_base, node)
        lx.expression = f"bs[0] * {coord[0]}"
        ly.expression = f"bs[1] * {coord[1]}"
        lz.expression = "sl * 0.5"

        quaternion_drivers = add_sample_node_quaternion_drivers(cam_base, node)
        for (i, axis) in enumerate(['w', 'x', 'y', 'z']):
            driver = quaternion_drivers[i]
            driver.expression = f"get_quadrilateral_hexahedron_camera_node_quaternion_rotation(fs, bs, sl, {cx}, {cy}).{axis}"
        
    return cam_base
