"""
A Blender addon that makes it easy to work with NeRF Datasets
"""

bl_info = {
    "name": "TurboNeRF",
    # Do not break this line, otherwise the addon can not be activated!
    "description": "An artistic tool for working with NeRFs in Blender",
    "author": "James Perlman",
    "version": (0, 0, 19),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > TurboNeRF",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View",
}

import bpy
import importlib
from turbo_nerf.effects.panels.spatial_effects_panel import NeRFSpatialEffectsPanel

from turbo_nerf.panels.nerf_object_panel import NeRFObjectPanel


from .utility import developer_utility
importlib.reload(developer_utility)
modules = developer_utility.setup_addon_modules(
    __path__, __name__, "bpy" in locals()
)


# The root dir is Blenders addon folder.
# Therefore, we need the "turbo_nerf" specifier for this addon
from turbo_nerf.blender_utility.logging_utility import log_report
from turbo_nerf.panels.nerf_3dview_panels.index import register_nerf_3dview_panels, unregister_nerf_3dview_panels
from turbo_nerf.registration.registration import Registration


from turbo_nerf.renderer.nerf_snapshot_manager import NeRFSnapshotManager
from turbo_nerf.constants import NERF_PATH_ID

@bpy.app.handlers.persistent
def load_handler(dummy):
    Registration.register_drivers()
    

def register():
    """Register importers, exporters and panels."""

    Registration.register_importers()
    Registration.register_exporters()
    bpy.utils.register_class(NeRFObjectPanel)
    bpy.utils.register_class(NeRFSpatialEffectsPanel)
    register_nerf_3dview_panels()

    bpy.app.handlers.load_post.append(load_handler)
    Registration.register_misc_components()
    log_report("INFO", "Registered {} with {} modules".format(bl_info["name"], len(modules)))


def unregister_drivers():
    Registration.unregister_drivers()


def unregister():
    """Unregister importers, exporters and panels."""

    Registration.unregister_importers()
    Registration.unregister_exporters()
    unregister_nerf_3dview_panels()
    
    bpy.utils.unregister_class(NeRFObjectPanel)
    bpy.utils.unregister_class(NeRFSpatialEffectsPanel)

    bpy.app.handlers.load_post.remove(load_handler)
    Registration.unregister_misc_components()

    log_report("INFO", "Unregistered {}".format(bl_info["name"]))


if __name__ == "__main__":
    log_report("INFO", "main called")
