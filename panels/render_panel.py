import bpy
import functools
import numpy as np
import math
import mathutils

def add_empty(name, collection=None, type='PLAIN_AXES'):
    """Add an empty to the scene."""
    if collection is None:
        collection = bpy.context.collection
    empty_obj = bpy.data.objects.new(name, None)
    empty_obj.empty_display_type = type
    collection.objects.link(empty_obj)
    return empty_obj

# cam_node = add_empty('foobar', type='SINGLE_ARROW')


# https://www.desmos.com/calculator/gxvsrnpd0d


# arc_t is normalized from [0.5, 0.5] - when arc_t is 0.5, we are at the point on the circle furthest from the origin
def walk_along_circle(curvature: float, linear_len: float, arc_len: float):
    
    arc_t = arc_len / (2.0 * linear_len)

    if arc_t == 0.0 or linear_len == 0.0:
        x, y = 0.0, 0.0
    
    elif curvature == 0.0:
        x = linear_len * arc_t
        y = 0.0
    
    else:
        tpc = 2.0 * math.pi * curvature
        s_tpc = linear_len / tpc
        x = s_tpc * math.sin(tpc * arc_t)
        y = -s_tpc * math.cos(tpc * arc_t) + linear_len / tpc
    
    return x, y


# z+ is forward
def walk_along_sphere(curvature: float, maximum_linear_len: float, azimuth: float, arc_len: float):
    r, z = walk_along_circle(curvature, maximum_linear_len, arc_len)
    
    x = r * math.cos(azimuth)
    y = r * math.sin(azimuth)
    
    return x, y, z


def get_spherical_quadrilateral_camera_node_location(curvature, maximum_linear_len, gx, gy):
    r = math.sqrt(gx**2 + gy**2)
    a = math.atan2(gy, gx)
    
    (x, y, z) = walk_along_sphere(curvature, maximum_linear_len, a, r)
    return mathutils.Vector([x, y, z])

def get_spherical_quadrilateral_camera_node_quaternion_rotation(curvature, maximum_linear_len, location):    
    normal_vec = mathutils.Vector([0, 0, 1])
    if curvature != 0.0:
        cz = maximum_linear_len / (2.0 * math.pi * curvature)
        sphere_center = mathutils.Vector([0, 0, cz])
        normal_vec = math.copysign(1.0, curvature) * (sphere_center - location).normalized()
    
    return normal_vec.to_track_quat('Z', 'X')

bpy.app.driver_namespace['get_spherical_quadrilateral_camera_node_location'] = get_spherical_quadrilateral_camera_node_location
bpy.app.driver_namespace['get_spherical_quadrilateral_node_quaternion_rotation'] = get_spherical_quadrilateral_camera_node_quaternion_rotation


# helpers for adding driver vars
def add_sensor_size_driver_vars(driver: bpy.types.Driver, cam_base):
    var_sw = driver.variables.new()
    var_sw.name = 'sw'
    var_sw.targets[0].id = cam_base
    var_sw.targets[0].data_path = '["sensor_width"]'

    var_sh = driver.variables.new()
    var_sh.name = 'sh'
    var_sh.targets[0].id = cam_base
    var_sh.targets[0].data_path = '["sensor_height"]'

def add_base_driver_vars(driver: bpy.types.Driver, cam_base):
    var_c = driver.variables.new()
    var_c.name = 'c'
    var_c.targets[0].id = cam_base
    var_c.targets[0].data_path = '["curvature"]'
    
    var_sd = driver.variables.new()
    var_sd.name = 'sd'
    var_sd.targets[0].id = cam_base
    var_sd.targets[0].data_path = '["sensor_diagonal"]'

def add_location_driver_vars(driver: bpy.types.Driver, cam_base):
    add_base_driver_vars(driver, cam_base)
    add_sensor_size_driver_vars(driver, cam_base)

def add_quaternion_driver_vars(driver: bpy.types.Driver, cam_base, cam_node):
    add_base_driver_vars(driver, cam_base)
    
    var_l = driver.variables.new()
    var_l.name = 'l'
    var_l.targets[0].id = cam_node
    var_l.targets[0].data_path = 'location'
    

# create points on spherical camera
rx, ry = 10, 10

coords = 2.0 * (np.stack(np.mgrid[:rx, :ry], -1) / [rx - 1, ry - 1] - [0.5, 0.5])
coords = coords.reshape(-1, coords.shape[-1])


curvature = 0.0
maximum_linear_len = 0.5 * math.sqrt(rx**2 + ry**2)

cam_base = add_empty('Spherical Quadrilateral Camera')
cam_base['curvature'] = curvature
prop = cam_base.id_properties_ui('curvature')
prop.update(precision=3, min=-1, max=1)

cam_base['sensor_width'] = 1.0
cam_base['sensor_height'] = 1.0

# add driver to calculate diagonal
cam_base['sensor_diagonal'] = math.sqrt(2)

sd = cam_base.driver_add('["sensor_diagonal"]').driver
add_sensor_size_driver_vars(sd, cam_base)
sd.expression = 'sqrt(sw**2 + sh**2)'


for coord in coords:
    cam_node = add_empty('camera_sample_point', type='PLAIN_AXES')
    cam_node.parent = cam_base
    cam_node.scale = [0.01, 0.01, 0.01]
    
    cam_arrow = add_empty('camera_arrow', type='SINGLE_ARROW')
    cam_arrow.parent = cam_node
    cam_arrow.rotation_mode = 'QUATERNION'
    cam_arrow.scale = [100, 100, 25]
    
    [cx, cy] = coord
    
    # drivers
    location_drivers = [fc.driver for fc in cam_node.driver_add('location')]
    quaternion_drivers = [fc.driver for fc in cam_arrow.driver_add('rotation_quaternion')]
    
    
    for (i, axis) in enumerate(['x', 'y', 'z']):
        add_location_driver_vars(location_drivers[i], cam_base)
        location_drivers[i].expression = f'get_spherical_quadrilateral_camera_node_location(c, sd, {cx} * sw, {cy} * sh).{axis}'
    
    for (i, axis) in enumerate(['w', 'x', 'y', 'z']):
        add_quaternion_driver_vars(quaternion_drivers[i], cam_base, cam_node)
        quaternion_drivers[i].expression = f'get_spherical_quadrilateral_node_quaternion_rotation(c, sd, l).{axis}'

    
    
        
    