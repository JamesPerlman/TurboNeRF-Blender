import bpy
from blender_nerf_tools.panels.nerf_panel_operators.import_dataset_operator import ImportNeRFDatasetOperator
from blender_nerf_tools.panels.nerf_panel_operators.train_nerf_operator import TrainNeRFOperator

class NeRFPanelProps(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D View"""
    n_steps_max: bpy.props.IntProperty(
        name="n_steps_max",
        description="Maximum number of steps to train.",
        default=2500,
        min=1,
        max=100000,
    )

class NeRFPanel(bpy.types.Panel):
    """Class that defines the NeRF panel in the 3D View"""

    bl_label = "TurboNeRF Panel"
    bl_idname = "VIEW3D_PT_blender_NeRF_render_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TurboNeRF"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True


    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""
        bpy.utils.register_class(NeRFPanelProps)
        bpy.types.Scene.nerf_panel_props = bpy.props.PointerProperty(type=NeRFPanelProps)
        
        bpy.utils.register_class(ImportNeRFDatasetOperator)
        bpy.utils.register_class(TrainNeRFOperator)


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ImportNeRFDatasetOperator)
        bpy.utils.unregister_class(NeRFPanelProps)
        bpy.utils.unregister_class(TrainNeRFOperator)
        del bpy.types.Scene.nerf_panel_props

    
    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        props = context.scene.nerf_panel_props

        layout = self.layout

        box = layout.box()
        box.label(text="Import")

        row = box.row()
        row.operator(ImportNeRFDatasetOperator.bl_idname, text="Import Dataset")

        box = layout.box()
        box.label(text="Train")

        #row = box.row()
        #row.operator(TrainNeRFOperator.bl_idname, text="Train NeRF")

        row = box.row()
        row.prop(props, "n_steps_max", text="Steps:")

        row = box.row()
        row.operator(TrainNeRFOperator.bl_idname, text="Start Training")

        row = box.row()
