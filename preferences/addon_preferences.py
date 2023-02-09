from bpy.types import (
    AddonPreferences,
    Operator,
    PropertyGroup,
)
from bpy.props import (   
    PointerProperty,
    StringProperty,
)
from bpy import utils
import bpy


# Thank you https://devtalk.blender.org/t/how-to-save-custom-user-preferences-for-an-addon/10362 

def fetch_pref(name: str):
    prefs = bpy.context.preferences.addons['blender_nerf_tools'].preferences
    if prefs is None:
        return None
    return prefs[name]

class TurboNeRFPreferences(AddonPreferences):
    bl_idname = "blender_nerf_tools"
    
    pylib_dir: StringProperty(
        name="PyTurboNeRF Directory",
        description = "Directory containing PyTurboNeRF.pyd",
        subtype='DIR_PATH',
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'pylib_dir')


def register_addon_preferences():
    utils.register_class(TurboNeRFPreferences)


def unregister_addon_preferences():
    utils.unregister_class(TurboNeRFPreferences)
