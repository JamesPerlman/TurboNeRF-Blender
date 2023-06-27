import bpy
from turbo_nerf.constants.raymarching import RAYMARCHING_MAX_STEP_SIZE, RAYMARCHING_MIN_STEP_SIZE
from turbo_nerf.panels.nerf_panel_operators.load_nerf_images_operator import LoadNeRFImagesOperator
from turbo_nerf.panels.nerf_panel_operators.reset_nerf_training_operator import ResetNeRFTrainingOperator
from turbo_nerf.panels.nerf_panel_operators.train_nerf_operator import TrainNeRFOperator
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

class NeRF3DViewTrainingPanelProps(bpy.types.PropertyGroup):
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

    update_id: bpy.props.IntProperty(
        name="update_id",
        description="Update the UI when this property changes.",
        default=0,
        min=0,
        max=1,
        update=update_ui,
    )

    # TODO: dynamic min/max based on the number of images
    image_load_progress: bpy.props.FloatProperty(
        name="image_load_progress",
        description="Progress of the dataset's image loading.",
        default=0.0,
        min=0.0,
        max=100.0,
        precision=1,
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

    # Trainer Settings

    show_training_settings: bpy.props.BoolProperty(
        name="show_training_settings",
        description="Show the training settings section.",
        default=False,
    )

    training_alpha_selection_threshold: bpy.props.FloatProperty(
        name="training_alpha_selection_threshold",
        description="Alpha threshold for selecting training pixels.",
        default=1.0,
        min=0.0,
        max=1.0,
        get=NeRFManager.bridge_obj_prop_getter("trainer", "alpha_selection_threshold", default=1.0),
        set=NeRFManager.bridge_obj_prop_setter("trainer", "alpha_selection_threshold"),
    )

    training_alpha_selection_probability: bpy.props.FloatProperty(
        name="training_alpha_selection_probability",
        description="Probability of selecting a training pixel less than the alpha threshold.",
        min=0.0,
        max=1.0,
        get=NeRFManager.bridge_obj_prop_getter("trainer", "alpha_selection_probability", default=1.0),
        set=NeRFManager.bridge_obj_prop_setter("trainer", "alpha_selection_probability"),
    )

    training_min_step_size: bpy.props.FloatProperty(
        name="training_min_step_size",
        description="Minimum step size for training.",
        min=RAYMARCHING_MIN_STEP_SIZE,
        max=RAYMARCHING_MAX_STEP_SIZE,
        get=NeRFManager.bridge_obj_prop_getter("trainer", "min_step_size", default=RAYMARCHING_MIN_STEP_SIZE),
        set=NeRFManager.bridge_obj_prop_setter("trainer", "min_step_size"),
        precision=6,
    )

    show_training_metrics: bpy.props.BoolProperty(
        name="show_training_metrics",
        description="Show the training metrics section.",
        default=False,
    )

    # Preview Section

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

register_global_timer = None
unregister_global_timer = None

def global_update_timer():
    context = bpy.context
    if nerf_props.needs_panel_update:
        ui_props = context.scene.nerf_training_panel_props

        # update training progress
        ui_props.training_progress = 100 * min(1, nerf_props.training_step / ui_props.n_steps_max)

        # update image load progress
        if nerf_props.n_images_total == 0:
            ui_props.image_load_progress = 0
        else:
            ui_props.image_load_progress = 100 * nerf_props.n_images_loaded / nerf_props.n_images_total
        
        ui_props.update_id = 1 - ui_props.update_id

        nerf_props.needs_panel_update = False
    
    if nerf_props.needs_timer_to_end:
        unregister_global_timer()
        nerf_props.needs_timer_to_end = False

    return TRAINING_TIMER_INTERVAL

is_global_timer_registered = lambda: bpy.app.timers.is_registered(global_update_timer)
register_global_timer = lambda: bpy.app.timers.register(global_update_timer, first_interval=0.1, persistent=True) if not is_global_timer_registered() else None
unregister_global_timer = lambda: bpy.app.timers.unregister(global_update_timer) if is_global_timer_registered() else None

class NeRF3DViewTrainingPanel(bpy.types.Panel):
    """Class that defines the NeRF Training panel in the 3D View"""

    bl_label = "Training"
    bl_idname = "VIEW3D_PT_blender_NeRF_training_panel"
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
        bpy.utils.register_class(LoadNeRFImagesOperator)
        bpy.utils.register_class(NeRF3DViewTrainingPanelProps)
        bpy.utils.register_class(ResetNeRFTrainingOperator)
        bpy.utils.register_class(TrainNeRFOperator)
        bpy.types.Scene.nerf_training_panel_props = bpy.props.PointerProperty(type=NeRF3DViewTrainingPanelProps)
        # cls.add_observers() won't work here, so we do it in draw()


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(LoadNeRFImagesOperator)
        bpy.utils.unregister_class(NeRF3DViewTrainingPanelProps)
        bpy.utils.unregister_class(ResetNeRFTrainingOperator)
        bpy.utils.unregister_class(TrainNeRFOperator)
            
        del bpy.types.Scene.nerf_training_panel_props

        cls.remove_observers()
        if bpy.app.timers.is_registered(global_update_timer):
            bpy.app.timers.unregister(global_update_timer)


    @classmethod
    def add_observers(cls):
        # do nothing if the observers have already been added
        if len(cls.observers) > 0:
            return

        bridge = NeRFManager.bridge()
        BBE = tn.BlenderBridgeEvent
        
        def on_training_start(args):
            # When training starts, we register a timer to update the UI
            register_global_timer()

        obid = bridge.add_observer(BBE.OnTrainingStart, on_training_start)
        cls.observers.append(obid)

        def on_training_stop(args):
            nerf_props.needs_panel_update = True
            nerf_props.needs_timer_to_end = True

        obid = bridge.add_observer(BBE.OnTrainingStop, on_training_stop)
        cls.observers.append(obid)   

        def on_training_step(metrics):
            nerf_props.training_step = metrics["step"]
            nerf_props.training_loss = metrics["loss"]
            nerf_props.n_rays_per_batch = metrics["n_rays"]

            # does training need to stop?
            if nerf_props.limit_training and nerf_props.training_step >= nerf_props.n_steps_max:
                NeRFManager.stop_training()
                nerf_props.needs_timer_to_end = True
            
            nerf_props.needs_panel_update = True

        obid = bridge.add_observer(BBE.OnTrainingStep, on_training_step)
        cls.observers.append(obid)

        def on_update_occupancy_grid(metrics):
            nerf_props.grid_percent_occupied = 100.0 * metrics["n_occupied"] / metrics["n_total"]
            nerf_props.needs_panel_update = True

        obid = bridge.add_observer(BBE.OnUpdateOccupancyGrid, on_update_occupancy_grid)
        cls.observers.append(obid)

        def on_images_load_start(args):
            
            nerf_props.n_images_total = args["n_total"]
            nerf_props.n_images_loaded = 0
            
            register_global_timer()
        
        obid = bridge.add_observer(BBE.OnTrainingImagesLoadStart, on_images_load_start)
        cls.observers.append(obid)

        def on_images_load_complete(args):
            nerf_props.needs_panel_update = True
            nerf_props.needs_timer_to_end = True
        
        obid = bridge.add_observer(BBE.OnTrainingImagesLoadComplete, on_images_load_complete)
        cls.observers.append(obid)

        def on_image_load(args):
            nerf_props.n_images_loaded = args["n_loaded"]
            nerf_props.n_images_total = args["n_total"]
            
            nerf_props.needs_panel_update = True

        obid = bridge.add_observer(BBE.OnTrainingImageLoaded, on_image_load)
        cls.observers.append(obid)

        def on_images_unload(args):
            nerf_props.n_images_loaded = 0
            nerf_props.n_images_total = 0
            nerf_props.training_step = 0
            nerf_props.training_loss = 0
            nerf_props.n_rays_per_batch = 0
            nerf_props.n_steps_max = 10000
            nerf_props.grid_percent_occupied = 100
            nerf_props.needs_panel_update = True
            nerf_props.needs_timer_to_end = True

            if not is_global_timer_registered():
                register_global_timer()

        obid = bridge.add_observer(BBE.OnTrainingImagesUnloaded, on_images_unload)
        cls.observers.append(obid)

        def on_training_reset(args):
            nerf_props.training_step = 0
            nerf_props.training_loss = 0
            nerf_props.n_rays_per_batch = 0
            nerf_props.grid_percent_occupied = 100
            nerf_props.needs_timer_to_end = True
            nerf_props.needs_panel_update = True

            if not is_global_timer_registered():
                register_global_timer()
                

        obid = bridge.add_observer(BBE.OnTrainingReset, on_training_reset)
        cls.observers.append(obid)


    @classmethod
    def remove_observers(cls):
        bridge = NeRFManager.bridge()
        for obid in cls.observers:
            bridge.remove_observer(obid)
        cls.observers.clear()


    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        NeRFManager.check_runtime()

        # kinda messy to call add_observers here but I'm not sure how else to do this.
        # TurboNeRF python lib doesn't load in cls.register()
        self.__class__.add_observers()

        ui_props = context.scene.nerf_training_panel_props

        layout = self.layout
        
        box = layout.box()
        box.label(text="Train")

        if NeRFManager.is_ready_to_train():

            row = box.row()
            row.operator(
                TrainNeRFOperator.bl_idname,
                text="Start Training" if not NeRFManager.is_training() else "Stop Training"
            )

            # we want to disable the Start Training button if we've already trained the scene up to the max number of steps
            row.enabled = not (ui_props.limit_training and nerf_props.training_step >= ui_props.n_steps_max)

            row = box.row()
            row.operator(ResetNeRFTrainingOperator.bl_idname)
            row.enabled = nerf_props.training_step > 0

        else:
            # if no images have been loaded yet, we show the Load Images button
            if nerf_props.n_images_total == 0:
                row = box.row()
                row.operator(
                    LoadNeRFImagesOperator.bl_idname,
                    text="Load Images"
                )
                row.enabled = NeRFManager.can_load_images()

            else:
                # otherwise assume images are currently loading
                row = box.row()
                row.label(text=f"Loaded {nerf_props.n_images_loaded} / {nerf_props.n_images_total} images")

                row = box.row()
                row.prop(ui_props, "image_load_progress", slider=True, text=f"% Done:")
                row.enabled = False

        # limit training checkbox
        row = box.row()
        row.prop(ui_props, "limit_training", text="Limit Training")
        
        # only show the max steps if limit training is checked
        if ui_props.limit_training:
            row = box.row()
            row.prop(ui_props, "n_steps_max", text="Max Steps")

            row = box.row()
            row.prop(ui_props, "training_progress", slider=True, text="% Done:")
            row.enabled = False

            row = box.row()
            row.label(text=f"Step: {nerf_props.training_step} / {ui_props.n_steps_max}")

            if nerf_props.training_step >= ui_props.n_steps_max:
                row = box.row()
                row.label(text="Training Complete!", icon="INFO")

        else:
            row = box.row()
            row.label(text=f"Step: {nerf_props.training_step}")
        
        # Training Settings
        row = box.row()
        row.prop(ui_props, "show_training_settings", text="Settings")

        if ui_props.show_training_settings:
            row = box.row()
            row.label(text="Training Pixel Selection")

            is_trainer_available = NeRFManager.bridge().trainer is not None

            row = box.row()
            row.prop(ui_props, "training_alpha_selection_threshold", text="Alpha Threshold")
            row.enabled = is_trainer_available

            row = box.row()
            row.prop(ui_props, "training_alpha_selection_probability", text="Selection Probability")
            row.enabled = is_trainer_available

            row = box.row()
            row.label(text="Raymarching")

            row = box.row()
            row.prop(ui_props, "training_min_step_size", text="Min Step Size")
            row.enabled = is_trainer_available
        
        # Training metrics

        row = box.row(align=True)
        row.prop(ui_props, "show_training_metrics", text="Metrics")

        if ui_props.show_training_metrics:
            row = box.row()
            row.label(text=f"Loss: {nerf_props.training_loss:.5f}")

            row = box.row()
            row.label(text=f"Rays: {nerf_props.n_rays_per_batch} per step")

            row = box.row()
            row.label(text=f"Grid: {nerf_props.grid_percent_occupied:.2f}% occupied")
