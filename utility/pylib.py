import importlib
from pathlib import Path
import sys

from blender_nerf_tools.preferences.addon_preferences import fetch_pref

tn = None

# this is just a glorified lazy loader
class PyTurboNeRFMetaClass(type):
    module = None

    def __getattr__(cls, name):
        if cls.module is None:
            pylib_dir = fetch_pref('pylib_dir')

            # sanity checks
            if pylib_dir is None:
                return
            
            if not Path(pylib_dir).exists():
                return
            
            if not Path(pylib_dir).is_dir():
                return

            # add to sys.path
            if pylib_dir not in sys.path:
                sys.path.append(pylib_dir)

        # import and return
        cls.module = importlib.import_module('PyTurboNeRF')
        return getattr(cls.module, name)

class PyTurboNeRF(metaclass=PyTurboNeRFMetaClass):
    def __getattr__(self, name):
        return getattr(type(self), name)
