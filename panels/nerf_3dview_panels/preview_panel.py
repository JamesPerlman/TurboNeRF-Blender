import bpy
from turbo_nerf.panels.nerf_panel_operators.preview_nerf_operator import PreviewNeRFOperator
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

TRAINING_TIMER_INTERVAL = 0.25

class NeRFProps:
    training_step = 0
    limit_training = True
    n_steps_max = 10000
    training_loss = 0.0
    n_rays_per_batch = 0
    grid_percent_occupied = 100.0
    n_images_loaded = 0
    n_images_total = 0
    needs_panel_update = False
    needs_timer_to_end = False

nerf_props = NeRFProps()

class NeRF3DViewPreviewPanelProps(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D View"""

    # Preview Section

    update_preview: bpy.props.BoolProperty(
        name="update_preview",
        description="Update the preview during training.",
        default=True,
    )

    time_between_preview_updates: bpy.props.FloatProperty(
        name="time_between_preview_updates",
        description="Time between preview updates in seconds.",
        default=1,
        min=0.1,
        max=10,
        precision=1,
    )

    def force_redraw(self, context):
        # TODO: we don't need to do this for all items
        for nerf in NeRFManager.get_all_nerfs():
            nerf.is_dataset_dirty = True

    show_near_planes: bpy.props.BoolProperty(
        name="show_near_planes",
        description="Show the near planes in the preview.",
        default=False,
        update=force_redraw,
    )

    show_far_planes: bpy.props.BoolProperty(
        name="show_far_planes",
        description="Show the far planes in the preview.",
        default=False,
        update=force_redraw,
    )

class NeRF3DViewPreviewPanel(bpy.types.Panel):
    """Class that defines the NeRF Preview panel in the 3D View"""

    bl_label = "TurboNeRF Preview Panel"
    bl_idname = "VIEW3D_PT_blender_NeRF_preview_panel"
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
        bpy.utils.register_class(PreviewNeRFOperator)
        bpy.utils.register_class(NeRF3DViewPreviewPanelProps)
        bpy.types.Scene.nerf_preview_panel_props = bpy.props.PointerProperty(type=NeRF3DViewPreviewPanelProps)


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(PreviewNeRFOperator)
        bpy.utils.unregister_class(NeRF3DViewPreviewPanelProps)
        del bpy.types.Scene.nerf_preview_panel_props

    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        ui_props = context.scene.nerf_preview_panel_props

        layout = self.layout
        box = layout.box()

        row = box.row()
        row.operator(PreviewNeRFOperator.bl_idname, text="Preview NeRF")

        row = box.row()
        row.prop(ui_props, "update_preview", text="Update Preview")

        if ui_props.update_preview:
            row = box.row()
            row.prop(ui_props, "time_between_preview_updates", text="Every (s):")
        
        row = box.row()
        row.prop(ui_props, "show_near_planes", text="Show Near Planes")

        row = box.row()
        row.prop(ui_props, "show_far_planes", text="Show Far Planes")
