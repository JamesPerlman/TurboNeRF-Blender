"""
A Blender addon that makes it easy to work with instant-ngp
"""

bl_info = {
    "name": "Instant-NGP Addon",
    # Do not break this line, otherwise the addon can not be activated!
    "description": "Allows you to work with instant-ngp scenes and export JSON for rendering.",
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

# The root dir is Blenders addon folder.
# Therefore, we need the "instant_ngp_tools" specifier for this addon
from instant_ngp_tools.blender_utility.logging_utility import log_report
from instant_ngp_tools.panels.instant_ngp_panel import InstantNGPPanel
from instant_ngp_tools.registration.registration import Registration

# from photogrammetry_importer.panels.view_3d_panel import OpenGLPanel
from .utility import developer_utility

importlib.reload(developer_utility)
modules = developer_utility.setup_addon_modules(
    __path__, __name__, "bpy" in locals()
)

def register():
    """Register importers, exporters and panels."""

    Registration.register_importers()
    Registration.register_exporters()

    bpy.utils.register_class(InstantNGPPanel)

    log_report("INFO", "Registered {} with {} modules".format(bl_info["name"], len(modules)))


def unregister():
    """Unregister importers, exporters and panels."""

    Registration.unregister_importers()
    Registration.unregister_exporters()

    bpy.utils.unregister_class(InstantNGPPanel)

    log_report("INFO", "Unregistered {}".format(bl_info["name"]))


if __name__ == "__main__":
    log_report("INFO", "main called")
