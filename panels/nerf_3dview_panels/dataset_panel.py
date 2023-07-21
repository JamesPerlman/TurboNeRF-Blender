import bpy
from pathlib import Path
from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj
from turbo_nerf.panels.nerf_panel_operators.export_dataset_operator import ExportNeRFDatasetOperator
from turbo_nerf.panels.nerf_panel_operators.import_dataset_operator import ImportNeRFDatasetOperator
from turbo_nerf.panels.nerf_panel_operators.unload_nerf_training_data_operator import UnloadNeRFTrainingDataOperator
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.panels.nerf_panel_operators.delete_nerf_dataset_operator import DeleteNeRFDatasetOperator


class NeRF3DViewDatasetPanelProps(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D View"""


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
        return NeRFManager.is_pylib_compatible()


    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""
        bpy.utils.register_class(ImportNeRFDatasetOperator)
        bpy.utils.register_class(ExportNeRFDatasetOperator)
        bpy.utils.register_class(UnloadNeRFTrainingDataOperator)
        bpy.utils.register_class(DeleteNeRFDatasetOperator)
        bpy.utils.register_class(NeRF3DViewDatasetPanelProps)
        bpy.types.Scene.nerf_dataset_panel_props = bpy.props.PointerProperty(type=NeRF3DViewDatasetPanelProps)
    

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ImportNeRFDatasetOperator)
        bpy.utils.unregister_class(ExportNeRFDatasetOperator)
        bpy.utils.unregister_class(UnloadNeRFTrainingDataOperator)
        bpy.utils.unregister_class(DeleteNeRFDatasetOperator)
        bpy.utils.unregister_class(NeRF3DViewDatasetPanelProps)
        del bpy.types.Scene.nerf_dataset_panel_props


    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        nerf_obj = get_active_nerf_obj(context)

        layout = self.layout
        box = layout.box()
        box.label(text="Dataset")

        row = box.row()
        row.operator(ImportNeRFDatasetOperator.bl_idname)

        row = box.row()
        row.operator(ExportNeRFDatasetOperator.bl_idname, text="Export Dataset")
        
        if nerf_obj is not None:
            nerf = NeRFManager.get_nerf_for_obj(nerf_obj)
            
            if nerf.dataset is not None:
                dataset_path = nerf.dataset.file_path
                parent_folder = Path(dataset_path).parent.name
                file_name = dataset_path.name

                row = box.row()
                row.label(text=f"{parent_folder}\{file_name}")

                row.operator(DeleteNeRFDatasetOperator.bl_idname, icon='X', text="")

