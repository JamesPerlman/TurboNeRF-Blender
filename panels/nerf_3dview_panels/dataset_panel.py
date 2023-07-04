import bpy
from turbo_nerf.panels.nerf_panel_operators.export_dataset_operator import ExportNeRFDatasetOperator
from turbo_nerf.panels.nerf_panel_operators.import_dataset_operator import ImportNeRFDatasetOperator
from turbo_nerf.panels.nerf_panel_operators.unload_nerf_training_data_operator import UnloadNeRFTrainingDataOperator


class NeRF3DViewDatasetPanelProps(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D View"""

    imported_dataset_path: bpy.props.StringProperty(
        name="Imported Dataset Path",
        default=""
    )

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
        bpy.utils.register_class(UnloadNeRFTrainingDataOperator)
        bpy.utils.register_class(NeRF3DViewDatasetPanelProps)
        bpy.types.Scene.nerf_dataset_panel_props = bpy.props.PointerProperty(type=NeRF3DViewDatasetPanelProps)
    

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ImportNeRFDatasetOperator)
        bpy.utils.unregister_class(ExportNeRFDatasetOperator)
        bpy.utils.unregister_class(UnloadNeRFTrainingDataOperator)
        bpy.utils.unregister_class(NeRF3DViewDatasetPanelProps)
        del bpy.types.Scene.nerf_dataset_panel_props


    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        layout = self.layout
        box = layout.box()
        box.label(text="Dataset")

        ui_props = context.scene.nerf_dataset_panel_props

        # Display the imported dataset's file path
        if ui_props.imported_dataset_path == "":
            row = box.row()
            row.operator(ImportNeRFDatasetOperator.bl_idname, text="Import Dataset")

        else:
            row = box.row()
            row.label(text=f"{ui_props.imported_dataset_path}")

            row = box.row()
            row.operator(UnloadNeRFTrainingDataOperator.bl_idname, text="Remove Dataset")
        
        row = box.row()
        row.operator(ExportNeRFDatasetOperator.bl_idname, text="Export Dataset")
