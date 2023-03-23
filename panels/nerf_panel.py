import bpy
from datetime import datetime
from turbo_nerf.panels.nerf_panel_operators.import_dataset_operator import ImportNeRFDatasetOperator
from turbo_nerf.panels.nerf_panel_operators.preview_nerf_operator import PreviewNeRFOperator
from turbo_nerf.panels.nerf_panel_operators.train_nerf_operator import TrainNeRFOperator
from turbo_nerf.utility.layout_utility import add_multiline_label
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

TRAINING_TIMER_INTERVAL = 0.5

class NeRFProps:
    training_step = 0
    limit_training = True
    n_steps_max = 10000
    training_loss = 0.0
    n_rays_per_batch = 0
    grid_percent_occupied = 100.0

nerf_props = NeRFProps()

class NeRFPanelProps(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D View"""

    def update_ui(self, context):
        return None
    
    def update_nerf_props(prop_name):
        def update_fn(self, context):
            setattr(nerf_props, prop_name, getattr(self, prop_name))
        return update_fn
    
    def update_n_steps_max(self, context):
        nerf_props.n_steps_max = self.n_steps_max
        self.training_progress = 100.0 * min(1.0, nerf_props.training_step / self.n_steps_max)
        self.update_training_progress(context)

    update_id: bpy.props.IntProperty(
        name="update_id",
        description="Update the UI when this property changes.",
        default=0,
        min=0,
        max=1,
        update=update_ui,
    )

    limit_training: bpy.props.BoolProperty(
        name="limit_training",
        description="Limit the number of steps to train.",
        default=nerf_props.limit_training,
        update=update_nerf_props("limit_training"),
    )

    n_steps_max: bpy.props.IntProperty(
        name="n_steps_max",
        description="Maximum number of steps to train.",
        default=nerf_props.n_steps_max,
        min=1,
        max=100000,
        update=update_n_steps_max
    )
    
    training_progress: bpy.props.FloatProperty(
        name="training_progress",
        description="Progress of the training.",
        default=0.0,
        min=0.0,
        max=100.0,
        precision=1,
    )

    show_training_metrics: bpy.props.BoolProperty(
        name="show_training_metrics",
        description="Show the training metrics section.",
        default=False,
    )

    update_preview: bpy.props.BoolProperty(
        name="update_preview",
        description="Update the preview during training.",
        default=True,
    )

    steps_between_preview_updates: bpy.props.IntProperty(
        name="steps_between_preview_updates",
        description="Number of steps between preview updates.",
        default=16,
        min=1,
        max=256,
    )


class NeRFPanel(bpy.types.Panel):
    """Class that defines the NeRF panel in the 3D View"""

    bl_label = "TurboNeRF Panel"
    bl_idname = "VIEW3D_PT_blender_NeRF_render_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TurboNeRF"

    observers = []
    panel_needs_update = False

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True


    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""
        bpy.utils.register_class(ImportNeRFDatasetOperator)
        bpy.utils.register_class(NeRFPanelProps)
        bpy.utils.register_class(PreviewNeRFOperator)
        bpy.utils.register_class(TrainNeRFOperator)
        bpy.types.Scene.nerf_panel_ui_props = bpy.props.PointerProperty(type=NeRFPanelProps)
        # cls.add_observers() won't work here, so we do it in draw()


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ImportNeRFDatasetOperator)
        bpy.utils.unregister_class(NeRFPanelProps)
        bpy.utils.unregister_class(PreviewNeRFOperator)
        bpy.utils.unregister_class(TrainNeRFOperator)
        del bpy.types.Scene.nerf_panel_ui_props
        cls.remove_observers()
        if bpy.app.timers.is_registered(cls.update_timer):
            bpy.app.timers.unregister(cls.update_timer)


    @classmethod
    def update_timer(cls):
        context = bpy.context
        if cls.panel_needs_update:
            ui_props = context.scene.nerf_panel_ui_props

            # update training progress
            training_progress = 100 * nerf_props.training_step / ui_props.n_steps_max
            ui_props.training_progress = min(100.0, training_progress)
            
            ui_props.update_id = 1 - ui_props.update_id

            cls.panel_needs_update = False

        return TRAINING_TIMER_INTERVAL


    @classmethod
    def add_observers(cls):
        # do nothing if the observers have already been added
        if len(cls.observers) > 0:
            return

        bridge = NeRFManager.bridge()
        BBE = tn.BlenderBridgeEvent

        timer_fn = cls.update_timer

        def on_training_started(args):
            # When training starts, we register a timer to update the UI
            if bpy.app.timers.is_registered(timer_fn):
                bpy.app.timers.unregister(timer_fn)
            
            bpy.app.timers.register(
                timer_fn,
                first_interval=1.0,
                persistent=True
            )

        obid = bridge.add_observer(BBE.OnTrainingStart, on_training_started)
        cls.observers.append(obid)

        def on_training_stopped(args):
            # unregister the timers added in on_training_started
            if bpy.app.timers.is_registered(timer_fn):
                bpy.app.timers.unregister(timer_fn)
            
            cls.panel_needs_update = True

        obid = bridge.add_observer(BBE.OnTrainingStop, on_training_stopped)
        cls.observers.append(obid)   

        def on_training_step(metrics):
            nerf_props.training_step = metrics["step"]
            nerf_props.training_loss = metrics["loss"]
            nerf_props.n_rays_per_batch = metrics["n_rays"]

            # does training need to stop?
            if nerf_props.limit_training and nerf_props.training_step >= nerf_props.n_steps_max:
                NeRFManager.stop_training()
            
            cls.panel_needs_update = True

        obid = bridge.add_observer(BBE.OnTrainingStep, on_training_step)
        cls.observers.append(obid)

        def on_update_occupancy_grid(metrics):
            nerf_props.grid_percent_occupied = 100.0 * metrics["n_occupied"] / metrics["n_total"]
            cls.panel_needs_update = True

        obid = bridge.add_observer(BBE.OnUpdateOccupancyGrid, on_update_occupancy_grid)
        cls.observers.append(obid)


    @classmethod
    def remove_observers(cls):
        bridge = NeRFManager.bridge()
        for obid in cls.observers:
            bridge.remove_observer(obid)
        cls.observers.clear()


    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        # kinda messy to call add_observers here but I'm not sure how else to do this.
        # TurboNeRF python lib doesn't load in cls.register()
        self.__class__.add_observers()

        ui_props = context.scene.nerf_panel_ui_props

        layout = self.layout
        
        if not NeRFManager.is_pylib_compatible():
            add_multiline_label(
                context=context,
                text=f"You have PyTurboNeRF version {NeRFManager.pylib_version()}, which is not compatible with this version of the TurboNeRF addon.  Please upgrade PyTurboNeRF to version {NeRFManager.required_pylib_version()}.",
                parent=layout
            )
            
            return
        
        self.dataset_section(layout, ui_props)

        self.training_section(layout, ui_props)

        self.preview_section(layout, ui_props)


    def dataset_section(self, layout, ui_props):
        box = layout.box()
        box.label(text="Dataset")

        row = box.row()
        row.operator(ImportNeRFDatasetOperator.bl_idname, text="Import Dataset")   


    def training_section(self, layout, ui_props):

        box = layout.box()
        box.label(text="Train")

        row = box.row()
        row.operator(
            TrainNeRFOperator.bl_idname,
            text="Start Training" if not NeRFManager.is_training() else "Stop Training"
        )

        # we want to disable the Start Training button if we've already trained the scene up to the max number of steps
        row.enabled = not (ui_props.limit_training and nerf_props.training_step >= ui_props.n_steps_max)

        # limit training checkbox
        row = box.row()
        row.prop(ui_props, "limit_training", text="Limit Training")
        
        # only show the max steps if limit training is checked
        if ui_props.limit_training:
            row = box.row()
            row.prop(ui_props, "n_steps_max", text="Max Steps")

            row = box.row()
            row.prop(ui_props, "training_progress", slider=True, text="")
            row.enabled = False

            row = box.row()
            row.label(text=f"Step: {nerf_props.training_step} / {ui_props.n_steps_max}")

            if nerf_props.training_step >= ui_props.n_steps_max:
                row = box.row()
                row.label(text="Training Complete!", icon="INFO")

        else:
            row = box.row()
            row.label(text=f"Step: {nerf_props.training_step}")
        
        # Training metrics
        
        row = box.row(align=True)
        row = row.split(factor=0.1)
        row.prop(ui_props, "show_training_metrics", icon_only=True, icon="TRIA_DOWN" if ui_props.show_training_metrics else "TRIA_RIGHT")
        row.label(text="Metrics")

        if ui_props.show_training_metrics:
            row = box.row()
            row.label(text=f"Loss: {nerf_props.training_loss:.5f}")

            row = box.row()
            row.label(text=f"Rays: {nerf_props.n_rays_per_batch} per batch")

            row = box.row()
            row.label(text=f"Grid: {nerf_props.grid_percent_occupied:.2f}% occupied")


    def preview_section(self, layout, ui_props):
        box = layout.box()
        box.label(text="Preview")

        row = box.row()
        row.prop(ui_props, "update_preview", text="Update Preview")

        if ui_props.update_preview:
            row = box.row()
            row.prop(ui_props, "steps_between_preview_updates", text="Every N Steps:")
        
        row = box.row()
        row.operator(PreviewNeRFOperator.bl_idname, text="Preview NeRF")

