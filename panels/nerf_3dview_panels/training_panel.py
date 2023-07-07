import bpy
from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj, get_closest_parent_of_type, get_nerf_obj_by_id, is_nerf_obj_type
from turbo_nerf.constants import OBJ_TYPE_NERF
from turbo_nerf.constants.raymarching import RAYMARCHING_MAX_STEP_SIZE, RAYMARCHING_MIN_STEP_SIZE
from turbo_nerf.panels.nerf_panel_operators.load_nerf_images_operator import LoadNeRFImagesOperator
from turbo_nerf.panels.nerf_panel_operators.reset_nerf_training_operator import ResetNeRFTrainingOperator
from turbo_nerf.panels.nerf_panel_operators.train_nerf_operator import TrainNeRFOperator
from turbo_nerf.panels.nerf_panel_operators.unload_nerf_training_data_operator import UnloadNeRFTrainingDataOperator
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

class GlobalProps:
    needs_panel_update = False
    needs_timer_to_end = False
    active_nerf_id = None

DEFAULT_NERF_PROPS = NeRFProps()

class NeRF3DViewTrainingPanelProps(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D View"""

    nerf_props = {}
    global_props = GlobalProps()

    def props_for_nerf_id(self, id: int) -> NeRFProps:
        if id not in self.nerf_props:
            self.nerf_props[id] = NeRFProps()
        
        return self.nerf_props[id]

    def props_for_nerf_obj(self, nerf_obj: bpy.types.Object) -> NeRFProps:
        if nerf_obj is None:
            return DEFAULT_NERF_PROPS

        nerf = NeRFManager.get_nerf_for_obj(nerf_obj)
        return self.props_for_nerf_id(nerf.id)

    def props_for_active_nerf(self, context) -> NeRFProps:
        return self.props_for_nerf_obj(get_active_nerf_obj(context))
    
    def clear_props_for_nerf_id(self, id):
        if id in self.nerf_props:
            del self.nerf_props[id]

    def update_ui(self, context):
        return None

    def nerf_prop_getter(prop_name, default):
        def get_fn(self):
            nerf_props = self.props_for_active_nerf(bpy.context)
            return getattr(nerf_props, prop_name, default)
        return get_fn
    
    def nerf_prop_setter(prop_name):
        def set_fn(self, value):
            nerf_props = self.props_for_active_nerf(bpy.context)
            setattr(nerf_props, prop_name, value)
        return set_fn

    update_id: bpy.props.IntProperty(
        name="update_id",
        description="Update the UI when this property changes.",
        default=0,
        min=0,
        max=1,
        update=update_ui,
    )

    def get_image_load_progress(self):
        nerf_props = self.props_for_active_nerf(bpy.context)
        # update image load progress
        if nerf_props.n_images_total == 0:
            return 0
        else:
            return 100 * nerf_props.n_images_loaded / nerf_props.n_images_total
    
    image_load_progress: bpy.props.FloatProperty(
        name="image_load_progress",
        description="Progress of the dataset's image loading.",
        default=0.0,
        min=0.0,
        max=100.0,
        precision=1,
        get=get_image_load_progress,
    )

    limit_training: bpy.props.BoolProperty(
        name="limit_training",
        description="Limit the number of steps to train.",
        default=DEFAULT_NERF_PROPS.limit_training,
        get=nerf_prop_getter("limit_training", DEFAULT_NERF_PROPS.limit_training),
        set=nerf_prop_setter("limit_training"),
    )

    n_steps_max: bpy.props.IntProperty(
        name="n_steps_max",
        description="Maximum number of steps to train.",
        default=DEFAULT_NERF_PROPS.n_steps_max,
        min=1,
        max=100000,
        get=nerf_prop_getter("n_steps_max", DEFAULT_NERF_PROPS.n_steps_max),
        set=nerf_prop_setter("n_steps_max"),
    )
    
    def get_training_progress(self):
        nerf_props = self.props_for_active_nerf(bpy.context)
        return 100.0 * min(1.0, nerf_props.training_step / self.n_steps_max)

    training_progress: bpy.props.FloatProperty(
        name="training_progress",
        description="Progress of the training.",
        default=0.0,
        min=0.0,
        max=100.0,
        precision=1,
        get=get_training_progress,
    )

    def get_training_enabled(self):
        nerf_obj = get_active_nerf_obj(bpy.context)
        return NeRFManager.is_training_enabled(nerf_obj)
            
    def set_training_enabled(self, value):
        nerf_obj = get_active_nerf_obj(bpy.context)

        if nerf_obj is None:
            return
        
        if value:
            NeRFManager.enable_training(nerf_obj)
        else:
            NeRFManager.disable_training(nerf_obj)

    enable_training: bpy.props.BoolProperty(
        name="enable_training",
        description="Enable training.",
        get=get_training_enabled,
        set=set_training_enabled,
    )

    # Trainer Settings

    def training_prop_getter(prop_name, default):
        def get_fn(self: bpy.types.PropertyGroup):
            nerf_obj = get_active_nerf_obj(bpy.context)

            if nerf_obj is None:
                return default
            
            trainer = NeRFManager.get_trainer_for_nerf_obj(nerf_obj)
            return getattr(trainer, prop_name, default)
    
        return get_fn

    def training_prop_setter(prop_name):
        def set_fn(self: bpy.types.PropertyGroup, value):
            nerf_obj = get_active_nerf_obj(bpy.context)

            if nerf_obj is None:
                return
            
            trainer = NeRFManager.get_trainer_for_nerf_obj(nerf_obj)
            setattr(trainer, prop_name, value)
        
        return set_fn

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
        get=training_prop_getter("alpha_selection_threshold", default=1.0),
        set=training_prop_setter("alpha_selection_threshold"),
    )

    training_alpha_selection_probability: bpy.props.FloatProperty(
        name="training_alpha_selection_probability",
        description="Probability of selecting a training pixel less than the alpha threshold.",
        min=0.0,
        max=1.0,
        get=training_prop_getter("alpha_selection_probability", default=1.0),
        set=training_prop_setter("alpha_selection_probability"),
    )

    training_min_step_size: bpy.props.FloatProperty(
        name="training_min_step_size",
        description="Minimum step size for training.",
        min=RAYMARCHING_MIN_STEP_SIZE,
        max=RAYMARCHING_MAX_STEP_SIZE,
        get=training_prop_getter("min_step_size", default=RAYMARCHING_MIN_STEP_SIZE),
        set=training_prop_setter("min_step_size"),
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

    time_between_preview_updates: bpy.props.IntProperty(
        name="time_between_preview_updates",
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

    # Danger Zone
    show_danger_zone: bpy.props.BoolProperty(
        name="show_danger_zone",
        description="Show the danger zone section.",
        default=False,
    )

register_global_timer = None
unregister_global_timer = None

def global_update_timer():
    context = bpy.context
    
    global_props = context.scene.nerf_training_panel_props.global_props
    
    if global_props.active_nerf_id is None:
        return TRAINING_TIMER_INTERVAL
    
    nerf_props = context.scene.nerf_training_panel_props.props_for_nerf_id(global_props.active_nerf_id)

    if global_props.needs_panel_update:
        ui_props = context.scene.nerf_training_panel_props
        
        ui_props.update_id = 1 - ui_props.update_id

        global_props.needs_panel_update = False
    
    if global_props.needs_timer_to_end:
        unregister_global_timer()
        global_props.needs_timer_to_end = False

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
        nerf_obj = get_active_nerf_obj(context)
        return nerf_obj is not None

    @classmethod
    @bpy.app.handlers.persistent
    def depsgraph_update_post_handler(cls, scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
        if len(scene.view_layers) == 0 or scene.view_layers[0].objects.active is None:
            return
        
        active_obj = scene.view_layers[0].objects.active
        nerf_obj = get_closest_parent_of_type(active_obj, OBJ_TYPE_NERF)

        id = None
        
        if nerf_obj is not None:
            nerf = NeRFManager.get_nerf_for_obj(nerf_obj)
            id = nerf.id
        
        scene.nerf_training_panel_props.global_props.active_nerf_id = id


    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""
        bpy.utils.register_class(LoadNeRFImagesOperator)
        bpy.utils.register_class(NeRF3DViewTrainingPanelProps)
        bpy.utils.register_class(ResetNeRFTrainingOperator)
        bpy.utils.register_class(TrainNeRFOperator)
        bpy.types.Scene.nerf_training_panel_props = bpy.props.PointerProperty(type=NeRF3DViewTrainingPanelProps)
        bpy.app.handlers.depsgraph_update_post.append(cls.depsgraph_update_post_handler)
        # cls.add_observers() won't work here, so we do it in draw()


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(LoadNeRFImagesOperator)
        bpy.utils.unregister_class(NeRF3DViewTrainingPanelProps)
        bpy.utils.unregister_class(ResetNeRFTrainingOperator)
        bpy.utils.unregister_class(TrainNeRFOperator)
            
        del bpy.types.Scene.nerf_training_panel_props
        bpy.app.handlers.depsgraph_update_post.remove(cls.depsgraph_update_post_handler)

        cls.remove_observers()
        if bpy.app.timers.is_registered(global_update_timer):
            bpy.app.timers.unregister(global_update_timer)


    @classmethod
    def add_observers(cls, context: bpy.types.Context):
        # do nothing if the observers have already been added
        if len(cls.observers) > 0:
            return

        bridge = NeRFManager.bridge()
        BBE = tn.BlenderBridgeEvent
        
        def on_training_start(args):
            # When training starts, we register a timer to update the UI
            global_props = context.scene.nerf_training_panel_props.global_props
            if global_props.needs_timer_to_end:
                global_props.needs_timer_to_end = False
            else:
                register_global_timer()

        obid = bridge.add_observer(BBE.OnTrainingStart, on_training_start)
        cls.observers.append(obid)

        def on_training_stop(args):
            global_props = context.scene.nerf_training_panel_props.global_props
            global_props.needs_panel_update = True
            global_props.needs_timer_to_end = True

        obid = bridge.add_observer(BBE.OnTrainingStop, on_training_stop)
        cls.observers.append(obid)   

        def on_training_step(args):
            nerf_id = args["id"]
            nerf_props = bpy.context.scene.nerf_training_panel_props.props_for_nerf_id(nerf_id)
            nerf_props.training_step = args["step"]
            nerf_props.training_loss = args["loss"]
            nerf_props.n_rays_per_batch = args["n_rays"]
            
            global_props = context.scene.nerf_training_panel_props.global_props

            # does training need to stop?
            if nerf_props.limit_training and nerf_props.training_step >= nerf_props.n_steps_max:
                nerf_obj = get_nerf_obj_by_id(bpy.context, nerf_id)
                NeRFManager.disable_training(nerf_obj)
            
            global_props.needs_panel_update = True

        obid = bridge.add_observer(BBE.OnTrainingStep, on_training_step)
        cls.observers.append(obid)

        def on_update_occupancy_grid(args):
            nerf_props = context.scene.nerf_training_panel_props.props_for_nerf_id(args["id"])
            nerf_props.grid_percent_occupied = 100.0 * args["n_occupied"] / args["n_total"]
            
            global_props = context.scene.nerf_training_panel_props.global_props
            global_props.needs_panel_update = True

        obid = bridge.add_observer(BBE.OnUpdateOccupancyGrid, on_update_occupancy_grid)
        cls.observers.append(obid)

        def on_images_load_start(args):
            nerf_props = context.scene.nerf_training_panel_props.props_for_nerf_id(args["id"])
            nerf_props.n_images_total = args["n_total"]
            nerf_props.n_images_loaded = 0
            
            register_global_timer()
        
        obid = bridge.add_observer(BBE.OnTrainingImagesLoadStart, on_images_load_start)
        cls.observers.append(obid)

        def on_images_load_complete(args):
            nerf_props = context.scene.nerf_training_panel_props.props_for_nerf_id(args["id"])
            global_props = context.scene.nerf_training_panel_props.global_props
            global_props.needs_panel_update = True
            if not NeRFManager.is_training():
                global_props.needs_timer_to_end = True
        
        obid = bridge.add_observer(BBE.OnTrainingImagesLoadComplete, on_images_load_complete)
        cls.observers.append(obid)

        def on_image_load(args):
            nerf_props = context.scene.nerf_training_panel_props.props_for_nerf_id(args["id"])
            nerf_props.n_images_loaded = args["n_loaded"]
            nerf_props.n_images_total = args["n_total"]
            
            global_props = context.scene.nerf_training_panel_props.global_props
            global_props.needs_panel_update = True

        obid = bridge.add_observer(BBE.OnTrainingImageLoaded, on_image_load)
        cls.observers.append(obid)

        def on_images_unload(args):
            nerf_props = context.scene.nerf_training_panel_props.props_for_nerf_id(args["id"])
            nerf_props.n_images_loaded = 0
            nerf_props.n_images_total = 0
            nerf_props.training_step = 0
            nerf_props.training_loss = 0
            nerf_props.n_rays_per_batch = 0
            nerf_props.n_steps_max = 10000
            nerf_props.grid_percent_occupied = 100

            global_props = context.scene.nerf_training_panel_props.global_props
            global_props.needs_panel_update = True
            global_props.needs_timer_to_end = True

            if not is_global_timer_registered():
                register_global_timer()

        obid = bridge.add_observer(BBE.OnTrainingImagesUnloaded, on_images_unload)
        cls.observers.append(obid)

        def on_training_reset(args):
            nerf_props = context.scene.nerf_training_panel_props.props_for_nerf_id(args["id"])
            nerf_props.training_step = 0
            nerf_props.training_loss = 0
            nerf_props.n_rays_per_batch = 0
            nerf_props.grid_percent_occupied = 100

            global_props = context.scene.nerf_training_panel_props.global_props
            global_props.needs_timer_to_end = True
            global_props.needs_panel_update = True

            if not is_global_timer_registered():
                register_global_timer()
                

        obid = bridge.add_observer(BBE.OnTrainingReset, on_training_reset)
        cls.observers.append(obid)

        def on_destroy_nerf(args):
            context.scene.nerf_training_panel_props.clear_props_for_nerf_id(args["id"])

        obid = bridge.add_observer(BBE.OnDestroyNeRF, on_destroy_nerf)
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
        self.__class__.add_observers(context)

        ui_props = context.scene.nerf_training_panel_props

        nerf_obj = get_active_nerf_obj(context)
        nerf_props = ui_props.props_for_nerf_obj(nerf_obj)
        is_trainer_available = NeRFManager.can_nerf_obj_train(nerf_obj)

        layout = self.layout
        
        box = layout.box()
        box.label(text="Train")

        # if no images have been loaded yet, we show the Load Images button
        if not NeRFManager.is_image_data_loaded(nerf_obj):
            if nerf_props.n_images_total == 0:
                row = box.row()
                row.operator(
                    LoadNeRFImagesOperator.bl_idname,
                    text="Load Images"
                )
                row.enabled = NeRFManager.can_load_images(nerf_obj)

            else:
                # otherwise assume images are currently loading
                row = box.row()
                row.label(text=f"Loaded {nerf_props.n_images_loaded} / {nerf_props.n_images_total} images")

                row = box.row()
                row.prop(ui_props, "image_load_progress", slider=True, text=f"% Done:")
                row.enabled = False

        # Start/Stop Training button
        row = box.row()
        row.operator(
            TrainNeRFOperator.bl_idname,
            text="Start Training" if not NeRFManager.is_training() else "Stop Training"
        )
        # we want to disable the Start Training button if we've already trained the scene up to the max number of steps
        max_training_step_reached = ui_props.limit_training and nerf_props.training_step >= ui_props.n_steps_max
        row.enabled = NeRFManager.can_any_nerf_train() and not max_training_step_reached

        # everything past this point is disabled if the trainer is not available
        if not is_trainer_available:
            return
        
        # enable training checkbox
        row = box.row()
        row.prop(ui_props, "enable_training", text="Train this NeRF")

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
        row.prop(ui_props, "show_training_settings", text="Trainer Settings")

        if ui_props.show_training_settings:
            row = box.row()
            row.label(text="Training Pixel Selection")

            row = box.row()
            row.prop(ui_props, "training_alpha_selection_threshold", text="Alpha Threshold")

            row = box.row()
            row.prop(ui_props, "training_alpha_selection_probability", text="Selection Probability")

            row = box.row()
            row.label(text="Raymarching")

            row = box.row()
            row.prop(ui_props, "training_min_step_size", text="Min Step Size")
        
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
        
        # Danger Zone

        row = box.row(align=True)
        row.prop(ui_props, "show_danger_zone", text="Danger Zone")

        if ui_props.show_danger_zone:
            row = box.row()
            row.operator(ResetNeRFTrainingOperator.bl_idname)

            row = box.row()
            row.operator(UnloadNeRFTrainingDataOperator.bl_idname)
