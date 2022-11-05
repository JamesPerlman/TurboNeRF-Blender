from pathlib import Path

import blender_nerf_tools.utility.load_ngp
import pyngp as ngp

__testbed__ = None
def testbed():
    global __testbed__
    if __testbed__ is None:
        __testbed__ = ngp.Testbed(ngp.TestbedMode.Nerf)
        __testbed__.shall_train = False
        __testbed__.fov_axis = 0
    return __testbed__

class NGPTestbedManager(object):
    has_snapshot = False
    @classmethod
    def load_snapshot(cls, snapshot_path: Path):
        cls.has_snapshot = True
        testbed().load_snapshot(str(snapshot_path))

    @classmethod
    def set_camera_matrix(cls, camera_matrix):
        testbed().set_nerf_camera_matrix(camera_matrix)
    
    @classmethod
    def render(cls, width, height):
        return testbed().render(width=width, height=height, spp=1)
