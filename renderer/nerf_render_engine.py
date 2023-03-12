import weakref
import bpy
import gpu
import bgl
import numpy as np

from turbo_nerf.blender_utility.nerf_render_manager import NeRFRenderManager
from turbo_nerf.renderer.utils.render_camera_utils import bl2nerf_cam
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

        self.prev_view_dimensions = np.array([0, 0])
        self.prev_region_camera_matrix = np.eye(4)[:3,:4]

        self.bridge = NeRFManager.bridge()
        self.event_observers = []
        
        self.add_event_observers()

    # Add bridge event observers
    def add_event_observers(self):
        BBE = tn.BlenderBridgeEvent

        # weak reference to self is used to avoid circular reference
        weak_self = weakref.ref(self)

        # OnTrainingStep
        def on_training_step():
            wself = weak_self()
            if wself is None:
                return
            step = wself.bridge.get_training_step()
            if step % 128 == 0:
                wself.rerequest_preview(flags=tn.RenderFlags.Preview)
        
        obid = self.bridge.add_observer(BBE.OnTrainingStep, on_training_step)
        self.event_observers.append(obid)

        # OnTrainingStopped
        def on_training_stopped():
            wself = weak_self()
            if wself is None:
                return
            if wself.bridge.is_rendering():
                return
            # wself.rerequest_preview(flags=tn.RenderFlags.Final)
        
        obid = self.bridge.add_observer(BBE.OnTrainingStopped, on_training_stopped)
        self.event_observers.append(obid)
    
        # OnPreviewProgress
        def on_preview_progress():
            wself = weak_self()
            if wself is None:
                return
            wself.bridge.enqueue_redraw()

        obid = self.bridge.add_observer(BBE.OnPreviewProgress, on_preview_progress)
        self.event_observers.append(obid)
        
        # OnPreviewComplete
        def on_preview_complete():
            wself = weak_self()
            if wself is None:
                return
            wself.bridge.enqueue_redraw()
        
        obid = self.bridge.add_observer(BBE.OnPreviewComplete, on_preview_complete)
        self.event_observers.append(obid)
        
        # OnRenderProgress
        def on_render_progress():
            wself = weak_self()
            if wself is None:
                return
            if wself.test_break():
                wself.bridge.cancel_render()
        
        obid = self.bridge.add_observer(BBE.OnRenderProgress, on_render_progress)
        self.event_observers.append(obid)
        
        # OnRenderComplete
        def on_request_redraw():
            wself = weak_self()
            if wself is None:
                return
            wself.tag_redraw()
        
        obid = self.bridge.add_observer(BBE.OnRequestRedraw, on_request_redraw)
        self.event_observers.append(obid)

    # Remove bridge event observers
    def remove_event_observers(self):
        for obs_id in self.event_observers:
            self.bridge.remove_observer(obs_id)
            print("Removed observer with id", obs_id)
        self.event_observers = []

    # When the render engine instance is destroyed, this is called. Clean up any
    # render engine data here, for example stopping running render threads.

    def __del__(self):
        print("del was called :(")
        self.remove_event_observers()
        pass

    # Notification handlers
    
    
    # This method re-requests the latest render
    def rerequest_preview(self, flags):
        if self.latest_camera is None:
            return
        self.bridge.request_preview(self.latest_camera, [NeRFManager.items[0].nerf], flags)

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        if self.is_preview:
            return
        
        # this just cancels the preview.  TODO: rename
        self.bridge.stop_training()
        self.bridge.cancel_preview()
        self.bridge.wait_for_runloop_to_stop()
        
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        size_x = int(scene.render.resolution_x * scale)
        size_y = int(scene.render.resolution_y * scale)

        dims = (size_x, size_y)

        active_cam = scene.camera
        # NeRFRenderManager.get_active_camera()
        camera = bl2nerf_cam(active_cam, dims)
        
        img = np.array(self.bridge.request_render(camera, [NeRFManager.items[0].nerf]))
        img = img.reshape((size_y, size_x, 4))

        # Here we write the pixel values to the RenderResult
        result = self.begin_result(0, 0, size_x, size_y)
        layer = result.layers[0].passes["Combined"]
        
        y_flipped = img[::-1, :, :].reshape((-1, 4))
        layer.rect = list(y_flipped)
        
        self.end_result(result)

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph: bpy.types.Depsgraph):
        self.tag_redraw()

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
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

        camera = bl2nerf_cam(current_region3d, dimensions)
        
        # Determine if the user initiated this view_draw call
        
        new_region_camera_matrix = np.array(camera.transform)
        user_initiated = np.not_equal(self.prev_region_camera_matrix, camera.transform).any()
        self.prev_region_camera_matrix = new_region_camera_matrix

        if user_initiated:
            flags = tn.RenderFlags.Preview
            if not NeRFManager.is_training():
                flags = flags | tn.RenderFlags.Final

            self.bridge.request_preview(camera, [NeRFManager.items[0].nerf], flags)
                    
        scene = depsgraph.scene

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE_MINUS_SRC_ALPHA)
        self.bind_display_space_shader(scene)
        
        self.bridge.draw()
        self.unbind_display_space_shader()
        bgl.glDisable(bgl.GL_BLEND)

        self.latest_camera = camera


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

