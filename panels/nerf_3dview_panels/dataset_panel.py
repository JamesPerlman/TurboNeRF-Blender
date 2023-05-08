import bpy
from turbo_nerf.panels.nerf_panel_operators.export_dataset_operator import ExportNeRFDatasetOperator
from turbo_nerf.panels.nerf_panel_operators.import_dataset_operator import ImportNeRFDatasetOperator


class NeRF3DViewDatasetPanel(bpy.types.Panel):
    """Class that defines the NeRF panel in the 3D View"""

    bl_label = "Datasets (JSON)"
    bl_idname = "VIEW3D_PT_blender_NeRF_dataset_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TurboNeRF"

    observers = []

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True


    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""
        bpy.utils.register_class(ImportNeRFDatasetOperator)
        bpy.utils.register_class(ExportNeRFDatasetOperator)
        # cls.add_observers() won't work here, so we do it in draw()


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ImportNeRFDatasetOperator)
        bpy.utils.unregister_class(ExportNeRFDatasetOperator)
        cls.remove_observers()



    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        layout = self.layout
        box = layout.box()

        row = box.row()
        row.operator(ImportNeRFDatasetOperator.bl_idname, text="Import Dataset")

        row = box.row()
        row.operator(ExportNeRFDatasetOperator.bl_idname, text="Export Dataset")
