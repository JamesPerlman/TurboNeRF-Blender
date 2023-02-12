import bpy
import numpy as np
from pathlib import Path

from blender_nerf_tools.blender_utility.object_utility import add_cube, add_empty
from blender_nerf_tools.blender_utility.obj_type_utility import get_nerf_obj_type
from blender_nerf_tools.constants import (
    OBJ_TYPE_ID,
    OBJ_TYPE_NERF,
    NERF_AABB_CENTER_ID,
    NERF_AABB_SIZE_ID,
    NERF_OPACITY_ID,
    NERF_PATH_ID,
)

def add_snapshot_aabb_cube_drivers(base:  bpy.types.Object, cube: bpy.types.Object):
    [lx, ly, lz] = [fc.driver for fc in cube.driver_add("location")]

    for i, driver in enumerate([lx, ly, lz]):
        # c is for center
        var_c = driver.variables.new()
        var_c.name = "c"
        var_c.targets[0].id = base
        var_c.targets[0].data_path = f'["{NERF_AABB_CENTER_ID}"]'

        driver.expression = f"c[{i}]"
    
    [sx, sy, sz] = [fc.driver for fc in cube.driver_add("scale")]

    for i, driver in enumerate([sx, sy, sz]):
        # s is for size
        var_s = driver.variables.new()
        var_s.name = "s"
        var_s.targets[0].id = base
        var_s.targets[0].data_path = f'["{NERF_AABB_SIZE_ID}"]'

        driver.expression = f"s[{i}]"


class NeRFSnapshotManager():

    @classmethod
    def get_all_snapshots(cls):
        return [obj for obj in bpy.data.objects if cls.is_nerf_snapshot(obj)]

    @classmethod
    def is_nerf_snapshot(cls, obj):
        return get_nerf_obj_type(obj) == OBJ_TYPE_NERF
    
    @classmethod
    def add_snapshot(cls, snapshot_path: Path, collection=None):
        snapshot_base: bpy.types.Object = add_empty("NeRF Snapshot", collection=collection, type='ARROWS')
        snapshot_base[OBJ_TYPE_ID] = OBJ_TYPE_NERF

        # TODO: copy snapshot into blender project folder?
        snapshot_base[NERF_PATH_ID] = str(snapshot_path.absolute())
    
        # TODO: load snapshot AABB from snapshot file
        snapshot_base[NERF_AABB_CENTER_ID] = [0.0, 0.0, 0.0]
        prop = snapshot_base.id_properties_ui(NERF_AABB_CENTER_ID)
        
        snapshot_base[NERF_AABB_SIZE_ID] = [8.0, 8.0, 8.0]

        # TODO: set correct min and max for AABB cropping
        prop = snapshot_base.id_properties_ui(NERF_AABB_SIZE_ID)
        prop.update(min=0.0, max=16.0)

        snapshot_base[NERF_OPACITY_ID] = 1.0
        prop = snapshot_base.id_properties_ui(NERF_OPACITY_ID)
        prop.update(min=0.0, max=1.0)

        # create AABB cube
        aabb_cube = add_cube("AABB Cube", size=1.0, collection=collection)
        aabb_cube.parent = snapshot_base
        aabb_cube.display_type = 'BOUNDS'

        add_snapshot_aabb_cube_drivers(snapshot_base, aabb_cube)
