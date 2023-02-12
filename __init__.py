"""
A Blender addon that makes it easy to work with NeRF Datasets
"""

bl_info = {
    "name": "Blender NeRF Tools",
    # Do not break this line, otherwise the addon can not be activated!
    "description": "Allows you to work with NeRF datasets.",
    "author": "James Perlman",
    "version": (0, 0, 1),
    "blender": (3, 0, 0),
    "location": "File/Import and File/Export",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export",
}

import bpy
import importlib


from .utility import developer_utility
importlib.reload(developer_utility)
modules = developer_utility.setup_addon_modules(
    __path__, __name__, "bpy" in locals()
)


# The root dir is Blenders addon folder.
# Therefore, we need the "blender_nerf_tools" specifier for this addon
from blender_nerf_tools.blender_utility.logging_utility import log_report
from blender_nerf_tools.panels.nerf_panel import NeRFPanel
from blender_nerf_tools.registration.registration import Registration


from blender_nerf_tools.renderer.nerf_snapshot_manager import NeRFSnapshotManager
from blender_nerf_tools.constants import NERF_PATH_ID

@bpy.app.handlers.persistent
def load_handler(dummy):
    Registration.register_drivers()
    

def register():
    """Register importers, exporters and panels."""

    Registration.register_importers()
    Registration.register_exporters()

    # bpy.utils.register_class(NeRFTrainingPanel)
    # bpy.utils.register_class(NeRFRenderPanel)
    bpy.utils.register_class(NeRFPanel)
    
    bpy.app.handlers.load_post.append(load_handler)
    Registration.register_misc_components()
    log_report("INFO", "Registered {} with {} modules".format(bl_info["name"], len(modules)))


def unregister_drivers():
    Registration.unregister_drivers()


def unregister():
    """Unregister importers, exporters and panels."""

    Registration.unregister_importers()
    Registration.unregister_exporters()

    # bpy.utils.unregister_class(NeRFTrainingPanel)
    # bpy.utils.unregister_class(NeRFRenderPanel)
    bpy.utils.unregister_class(NeRFPanel)

    bpy.app.handlers.load_post.remove(load_handler)
    Registration.unregister_misc_components()

    log_report("INFO", "Unregistered {}".format(bl_info["name"]))


if __name__ == "__main__":
    log_report("INFO", "main called")
