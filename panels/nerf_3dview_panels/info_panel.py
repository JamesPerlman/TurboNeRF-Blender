import bpy
from turbo_nerf.utility.layout_utility import add_multiline_label
from turbo_nerf.utility.nerf_manager import NeRFManager
# from turbo_nerf.utility.pylib import PyTurboNeRF as tn

class NeRF3DViewInfoPanel(bpy.types.Panel):
    """Debug info panel for TurboNeRF."""

    bl_label = "Info"
    bl_idname = "VIEW3D_PT_blender_NeRF_info_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TurboNeRF"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True

    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        layout = self.layout
        
        is_runtime_ready = NeRFManager.check_runtime()

        if not is_runtime_ready:
            add_multiline_label(
                context=context,
                parent=layout,
                text="The PyTurboNeRF runtime could not be loaded.  Please go to Window > Toggle System Console to check for any errors.",
                icon="ERROR"
            )

            return

        if not NeRFManager.is_pylib_compatible():
            add_multiline_label(
                context=context,
                parent=layout,
                text=f"You have PyTurboNeRF version {NeRFManager.pylib_version()}, which is not compatible with this version of the TurboNeRF addon.  Please upgrade PyTurboNeRF to version {NeRFManager.required_pylib_version()}.",
                icon="ERROR"
            )
            
            return
        
        box = layout.box()
        row = box.row()
        row.label(text=f"Version {NeRFManager.pylib_version()}")

