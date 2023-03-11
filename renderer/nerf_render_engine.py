import bpy
import gpu
import bgl
import numpy as np

from turbo_nerf.blender_utility.nerf_render_manager import NeRFRenderManager
from turbo_nerf.renderer.utils.render_camera_utils import bl2nerf_cam
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.notification_center import NotificationCenter
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

        self.render_engine = NeRFManager.bridge()
        self.render_engine.set_request_redraw_callback(self.tag_redraw)
        NotificationCenter.default().add_observer("TRAIN_STEP", self.on_train_step)
        NotificationCenter.default().add_observer("TRAINING_STOPPED", self.on_training_stopped)
    

    # When the render engine instance is destroyed, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        pass

    # Notification handlers
    
    def on_train_step(self, step):
        if step % 128 == 0:
            flags = tn.RenderFlags.Preview
            print("on_train flags = ", flags)
            self.rerequest_render(flags=tn.RenderFlags.Preview)
    
    def on_training_stopped(self):
        self.rerequest_render(flags=tn.RenderFlags.Final)
    
    # This method re-requests the latest render
    def rerequest_render(self, flags):
        self.render_engine.request_render(self.latest_camera, [NeRFManager.items[0].nerf], flags)

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        if self.is_preview:
            return

        # this just cancels the preview.  TODO: rename
        self.render_engine.cancel_render()
        
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        size_x = int(scene.render.resolution_x * scale)
        size_y = int(scene.render.resolution_y * scale)

        dims = (size_x, size_y)

        active_cam = scene.camera
        # NeRFRenderManager.get_active_camera()
        camera = bl2nerf_cam(active_cam, dims)
        
        img = np.array(self.render_engine.render_final(camera, [NeRFManager.items[0].nerf]))
        # reverse pixels
        # reverse img

        # Here we write the pixel values to the RenderResult
        result = self.begin_result(0, 0, size_x, size_y)
        layer = result.layers[0].passes["Combined"]
        
        layer.rect = list(img.reshape((-1, 4)))
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
        
        self.render_engine.resize_render_surface(region.width, region.height)
        
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

            self.render_engine.request_render(camera, [NeRFManager.items[0].nerf], flags)
                    
        scene = depsgraph.scene

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE_MINUS_SRC_ALPHA)
        self.bind_display_space_shader(scene)
        
        self.render_engine.draw()
        
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

