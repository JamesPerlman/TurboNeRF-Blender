import bpy
from datetime import datetime
from turbo_nerf.panels.nerf_panel_operators.import_dataset_operator import ImportNeRFDatasetOperator
from turbo_nerf.panels.nerf_panel_operators.train_nerf_operator import TrainNeRFOperator
from turbo_nerf.utility.layout_utility import add_multiline_label
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

TRAINING_TIMER_INTERVAL = 0.5

class NeRFPanelProps(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D View"""

    def update_ui(self, context):
        return None

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
        default=True,
    )

    n_steps_max: bpy.props.IntProperty(
        name="n_steps_max",
        description="Maximum number of steps to train.",
        default=10000,
        min=1,
        max=100000,
    )
    
    training_progress: bpy.props.FloatProperty(
        name="training_progress",
        description="Progress of the training.",
        default=0.0,
        min=0.0,
        max=100.0,
        precision=1,
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

    training_step: bpy.props.IntProperty(
        name="training_step",
        description="Current training step.",
        default=0,
        min=0,
        max=1000000,
    )

    training_loss: bpy.props.FloatProperty(
        name="training_loss",
        description="Current training loss.",
        default=0.0,
        min=0.0,
        max=1000000.0,
        precision=5,
    )

class NeRFPanel(bpy.types.Panel):
    """Class that defines the NeRF panel in the 3D View"""

    bl_label = "TurboNeRF Panel"
    bl_idname = "VIEW3D_PT_blender_NeRF_render_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TurboNeRF"

    observers = []
    training_step = 0
    training_loss = 0.0
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
        bpy.utils.register_class(TrainNeRFOperator)
        bpy.types.Scene.nerf_panel_props = bpy.props.PointerProperty(type=NeRFPanelProps)
        # cls.add_observers() won't work here, so we do it in draw()


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ImportNeRFDatasetOperator)
        bpy.utils.unregister_class(NeRFPanelProps)
        bpy.utils.unregister_class(TrainNeRFOperator)
        del bpy.types.Scene.nerf_panel_props
        cls.remove_observers()
        if bpy.app.timers.is_registered(cls.update_timer):
            bpy.app.timers.unregister(cls.update_timer)


    @classmethod
    def update_timer(cls):
        context = bpy.context
        if cls.panel_needs_update:
            props = context.scene.nerf_panel_props
            props.update_id = 1 - props.update_id
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

        obid = bridge.add_observer(BBE.OnTrainingStop, on_training_stopped)
        cls.observers.append(obid)   

        def on_training_step(metrics):
            cls.training_step = metrics["step"]
            cls.training_loss = metrics["loss"]
            cls.panel_needs_update = True

        obid = bridge.add_observer(BBE.OnTrainingStep, on_training_step)
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

        props = context.scene.nerf_panel_props

        layout = self.layout
        
        if not NeRFManager.is_pylib_compatible():
            add_multiline_label(
                context=context,
                text=f"You have PyTurboNeRF version {NeRFManager.pylib_version()}, which is not compatible with this version of the TurboNeRF addon.  Please upgrade PyTurboNeRF to version {NeRFManager.required_pylib_version()}.",
                parent=layout
            )
            
            return
        
        self.dataset_section(layout, props)

        self.training_section(layout, props)

        self.preview_section(layout, props)


    def dataset_section(self, layout, props):
        box = layout.box()
        box.label(text="Dataset")

        row = box.row()
        row.operator(ImportNeRFDatasetOperator.bl_idname, text="Import Dataset")   


    def training_section(self, layout, props):

        box = layout.box()
        box.label(text="Train")

        row = box.row()
        row.operator(
            TrainNeRFOperator.bl_idname,
            text="Start Training" if not NeRFManager.is_training() else "Stop Training"
        )

        row = box.row()
        row.prop(props, "limit_training", text="Limit Training")
        
        # only show the max steps if limit training is checked
        if props.limit_training:
            row = box.row()
            row.prop(props, "n_steps_max", text="Max Steps")

            row = box.row()
            row.prop(props, "training_progress", slider=True, text="")
            row.enabled = False

            row = box.row()
            row.label(text=f"Step: {self.training_step} / {props.n_steps_max}")

        else:
            row = box.row()
            row.label(text=f"Step: {self.training_step}")


    def preview_section(self, layout, props):
        box = layout.box()
        box.label(text="Preview")

        row = box.row()
        row.prop(props, "update_preview", text="Update Preview")

        if props.update_preview:
            row = box.row()
            row.prop(props, "steps_between_preview_updates", text="Steps Between Updates")
        
