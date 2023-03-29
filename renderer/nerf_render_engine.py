import ctypes
from time import sleep, time
import weakref
import bpy
import bgl
import numpy as np
from turbo_nerf.blender_utility.obj_type_utility import get_closest_parent_of_type, get_nerf_obj_type
from turbo_nerf.constants import CAMERA_INDEX_ID, NERF_ITEM_IDENTIFIER_ID, OBJ_TYPE_NERF, OBJ_TYPE_TRAIN_CAMERA

from turbo_nerf.utility.render_camera_utils import bl2nerf_cam, bl2nerf_cam_train, camera_with_flipped_y
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

import threading

class TurboNeRFRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "TURBO_NERF_RENDERER"
    bl_label = "TurboNeRF"
    bl_use_eevee_viewport = True
    bl_use_preview = True
    bl_use_exclude_layers = True
    bl_use_custom_freestyle = True

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.render_lock = threading.Lock()
        self.scene_data = None
        self.is_rendering = False
        self.redraw_from_render_result = False
        self.cancel_current_render = False
        self.current_region3d: bpy.types.RegionView3D = None
        self.latest_camera = None
        self.render_thread = None
        self.write_to_surface = None
        self.surface_is_allocated = False

        self.prev_view_dims = (0, 0)

        self.bridge = NeRFManager.bridge()
        self.event_observers = []
        
        self.add_event_observers()

    # Add bridge event observers
    def add_event_observers(self):
        BBE = tn.BlenderBridgeEvent

        # weak reference to self is used to avoid circular reference
        weak_self = weakref.ref(self)

        # OnTrainingStep
        def on_training_step(metrics):
            wself = weak_self()
            if wself is None:
                return
            step = metrics["step"]

            nerf_panel_props = bpy.context.scene.nerf_panel_ui_props
            if nerf_panel_props.update_preview and step % nerf_panel_props.steps_between_preview_updates == 0:
                wself.rerequest_preview(flags=tn.RenderFlags.Preview)
        
        obid = self.bridge.add_observer(BBE.OnTrainingStep, on_training_step)
        self.event_observers.append(obid)

        # OnTrainingStop
        def on_training_stop(args):
            wself = weak_self()
            if wself is None:
                return
            wself.rerequest_preview(flags=tn.RenderFlags.Final)
        
        obid = self.bridge.add_observer(BBE.OnTrainingStop, on_training_stop)
        self.event_observers.append(obid)
    
        # OnPreviewProgress
        def on_preview_progress(args):
            wself = weak_self()
            if wself is None:
                return
            wself.bridge.enqueue_redraw()

        obid = self.bridge.add_observer(BBE.OnPreviewProgress, on_preview_progress)
        self.event_observers.append(obid)
        
        # OnPreviewComplete
        def on_preview_complete(args):
            wself = weak_self()
            if wself is None:
                return
            wself.bridge.enqueue_redraw()
        
        obid = self.bridge.add_observer(BBE.OnPreviewComplete, on_preview_complete)
        self.event_observers.append(obid)
        
        # OnRenderComplete
        def on_request_redraw(args):
            wself = weak_self()
            if wself is None:
                return
            wself.tag_redraw()
        
        obid = self.bridge.add_observer(BBE.OnRequestRedraw, on_request_redraw)
        self.event_observers.append(obid)

    # Remove bridge event observers
    def remove_event_observers(self):
        if hasattr(self, "event_observers"):
            for obid in self.event_observers:
                self.bridge.remove_observer(obid)
            self.event_observers = []

    # When the render engine instance is destroyed, this is called. Clean up any
    # render engine data here, for example stopping running render threads.

    def __del__(self):
        self.remove_event_observers()
        pass

    def get_render_modifiers(self, context: bpy.types.Context):
        render_modifiers = tn.RenderModifiers()
        render_modifiers.properties = tn.RenderProperties()
        render_modifiers.properties.show_near_planes = True
        render_modifiers.properties.show_far_planes = True
        return render_modifiers

    # This method re-requests the latest render
    def rerequest_preview(self, flags):
        if self.latest_camera is None:
            return
        
        if len(NeRFManager.items) == 0:
            return
        
        modifiers = self.get_render_modifiers(bpy.context)
        self.bridge.request_preview(self.latest_camera, [NeRFManager.items[0].nerf], flags, modifiers)

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        
        # get properties
        scene = depsgraph.scene
        scene.frame_set(scene.frame_current) # found this in povray, said it was necessary
        scale = scene.render.resolution_percentage / 100.0
        size_x = int(scene.render.resolution_x * scale)
        size_y = int(scene.render.resolution_y * scale)

        dims = (size_x, size_y)

        # get camera
        active_cam = scene.camera
        
        if active_cam is None:
            # TODO: error?
            print("ERROR: No active camera during render!")
            return

        # convert to TurboNeRF camera
        camera = bl2nerf_cam(active_cam, dims)
        camera = camera_with_flipped_y(camera)

        # launch render request
        self.bridge.request_render(camera, [NeRFManager.items[0].nerf])
        
        # begin renter result
        result = self.begin_result(0, 0, size_x, size_y)

        # register render events
        render_events = []

        # OnRenderProgress
        def on_render_progress(args):
            # get latest from the render buffer
            rgba_buf = self.bridge.get_render_rgba()
            n_pixels = self.bridge.get_render_n_pixels()

            # this is a total hack from https://devtalk.blender.org/t/pass-a-render-result-as-a-numpy-array-to-bpy-types-renderengine/11615/8?u=jperl
            # and I love it :] thank you @Kinwailo

            # interpret the buffer as a numpy array (no copying!)
            rgba_view = memoryview(rgba_buf)
            img = np.asarray(rgba_view)

            # convert to raw data
            img = img.ctypes.data_as(ctypes.c_void_p)
            
            # copy image data into the renderpass.rect buffer!
            render_pass = result.layers[0].passes["Combined"]
            dst = render_pass.as_pointer() + 96
            dst = ctypes.cast(dst, ctypes.POINTER(ctypes.c_void_p))
            float_size = ctypes.sizeof(ctypes.c_float)
            ctypes.memmove(dst.contents, img, 4 * float_size * n_pixels)
    
            self.update_result(result)

            # update the progress bar
            self.update_progress(self.bridge.get_render_progress())
        
        # add OnRenderProgress observer
        event_id = self.bridge.add_observer(tn.BlenderBridgeEvent.OnRenderProgress, on_render_progress)
        render_events.append(event_id)

        # OnRenderComplete
        def on_render_complete(args):
            on_render_progress(None)

        # add OnRenderComplete observer
        event_id = self.bridge.add_observer(tn.BlenderBridgeEvent.OnRenderComplete, on_render_complete)
        render_events.append(event_id)

        # keep alive until render is complete
        while self.bridge.is_rendering():
            # check for cancel
            if self.test_break():
                self.bridge.cancel_render()
                break
            
            # I have no idea why, but this keeps blender responsive
            sleep(0.1)

        # end result
        self.end_result(result)
        
        # remove event observers
        for obid in render_events:
            self.bridge.remove_observer(obid)

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph: bpy.types.Depsgraph):
        for update in depsgraph.updates:
            if update.is_updated_transform:
                obj = update.id
                if not isinstance(obj, bpy.types.Object):
                    continue

                nerf_obj = get_closest_parent_of_type(obj, OBJ_TYPE_NERF)
                if nerf_obj is None:
                    continue
            
                if get_nerf_obj_type(obj) == OBJ_TYPE_TRAIN_CAMERA:
                    cam_obj = obj
                    nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]
                    nerf = NeRFManager.items[nerf_id].nerf
                    camera_idx = cam_obj[CAMERA_INDEX_ID]
                    nerf.dataset.set_camera_at(camera_idx, bl2nerf_cam_train(cam_obj))
                    nerf.is_dataset_dirty = True
                        
    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        print("view_draw()")
        # # Get viewport dimensions
        region = context.region
        dimensions = region.width, region.height
        
        self.bridge.resize_preview_surface(region.width, region.height)
        
        # Get current camera
        current_region3d: bpy.types.RegionView3D = None
        for area in context.screen.areas:
            area: bpy.types.Area
            if area.type == 'VIEW_3D':
                current_region3d = area.spaces.active.region_3d
        
        if current_region3d is None:
            return

        camera = bl2nerf_cam(current_region3d, dimensions, context)

        if camera is None:
            return
        
        # Determine if the user initiated this view_draw call
        nerf = NeRFManager.items[0].nerf
        
        has_new_camera = True if self.latest_camera is None else camera != self.latest_camera
        has_new_dims = dimensions != self.prev_view_dims

        user_initiated = has_new_camera or has_new_dims or nerf.is_dataset_dirty

        if user_initiated:
            flags = tn.RenderFlags.Preview
            if not NeRFManager.is_training(): # and not context.screen.is_animation_playing:
                flags = flags | tn.RenderFlags.Final

            modifiers = self.get_render_modifiers(context)

            self.bridge.request_preview(camera, [nerf], flags, modifiers)
                    
        scene = depsgraph.scene

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE_MINUS_SRC_ALPHA)
        self.bind_display_space_shader(scene)
        
        self.bridge.draw()
        self.unbind_display_space_shader()
        bgl.glDisable(bgl.GL_BLEND)

        self.latest_camera = camera
        self.prev_view_dims = dimensions


# RenderEngines also need to tell UI Panels that they are compatible with.
# We recommend to enable all panels marked as BLENDER_RENDER, and then
# exclude any panels that are replaced by custom panels registered by the
# render engine, or that are not supported.
def get_panels():
    exclude_panels = {
        'VIEWLAYER_PT_filter',
        'VIEWLAYER_PT_layer_passes',
    }

    panels = []
    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'COMPAT_ENGINES') and 'BLENDER_RENDER' in panel.COMPAT_ENGINES:
            if panel.__name__ not in exclude_panels:
                panels.append(panel)

    return panels


def register_nerf_render_engine():
    # Register the RenderEngine
    bpy.utils.register_class(TurboNeRFRenderEngine)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('TURBO_NERF_RENDERER')


def unregister_nerf_render_engine():
    bpy.utils.unregister_class(TurboNeRFRenderEngine)

    for panel in get_panels():
        if 'CUSTOM' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('TURBO_NERF_RENDERER')

