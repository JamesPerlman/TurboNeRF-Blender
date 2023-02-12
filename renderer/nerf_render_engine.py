import bpy
import gpu
import bgl
import numpy as np

from blender_nerf_tools.blender_utility.nerf_render_manager import NeRFRenderManager
from blender_nerf_tools.renderer.utils.render_camera_utils import NeRFRenderCamera, bl2nerf_cam
from blender_nerf_tools.utility.nerf_manager import NeRFManager

from blender_nerf_tools.utility.pylib import PyTurboNeRF as tn

import threading

MAX_MIP_LEVEL = 4
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
        self.scene_data = None
        self.is_painting = False
        self.is_rendering = False
        self.needs_to_redraw = False
        self.cancel_current_render = False
        self.current_region3d: bpy.types.RegionView3D = None
        self.prev_render_cam: NeRFRenderCamera = None
        self.render_thread = None
        self.write_to_surface = None
        self.surface_is_allocated = False

        self.prev_view_dimensions = np.array([0, 0])
        self.prev_region_camera_matrix = np.eye(4)

        self.renderer = tn.Renderer(batch_size=2<<20)
        self.surface = None

        tn.BlenderRenderEngine.init()
    

    # When the render engine instance is destroyed, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        pass

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        size_x = int(scene.render.resolution_x * scale)
        size_y = int(scene.render.resolution_y * scale)

        dims = (size_x, size_y)

        # Fill the render result with a flat color. The framebuffer is
        # defined as a list of pixels, each pixel itself being a list of
        # R,G,B,A values.
        # if self.is_preview:
        #    pass

        active_cam = NeRFRenderManager.get_active_camera()
        cam_props = bl2nerf_cam(active_cam, dims)
        # rect = NGPTestbedManager.request_render(cam_props, size_x, size_y, 0)

        # Here we write the pixel values to the RenderResult
        result = self.begin_result(0, 0, size_x, size_y)
        layer = result.layers[0].passes["Combined"]
        # layer.rect = list(rect.reshape((-1, 4)))
        self.end_result(result)

    def start_rendering(self, context: bpy.types.Context, depsgraph: bpy.types.Depsgraph):
        # start render thread
        if self.is_rendering:
            self.cancel_current_render = True
            return
    
        print("STARTING RENDER THREAD")
        self.is_rendering = True
        self.cancel_current_render = False

        # Get viewport dimensions
        region = context.region
        dimensions = region.width, region.height
        
        # Get current camera
        current_region3d: bpy.types.RegionView3D = None
        for area in context.screen.areas:
            area: bpy.types.Area
            if area.type == 'VIEW_3D':
                current_region3d = area.spaces.active.region_3d

        # create a render surface, if needed (or just resize it)
        if self.surface is None:
            self.surface = tn.OpenGLRenderSurface(region.width, region.height)
            self.surface.allocate()
        elif self.surface.width != region.width or self.surface.height != region.height:
            self.surface.resize(region.width, region.height)
            
        # Render thread
        def render():
            # Partial result & completion callback
            def on_render_result(is_done):
                if is_done:
                    self.is_rendering = False
                    self.needs_to_redraw = False
                else:
                    if not self.is_painting:
                        print("REDRAWING!")
                        self.needs_to_redraw = True
                        self.tag_redraw()
            
            # Cancellation poll
            def should_cancel_render():
                return self.cancel_current_render

            cam = bl2nerf_cam(current_region3d, dimensions)

            request = tn.RenderRequest(
                camera=cam,
                nerfs=[NeRFManager.items[0].nerf],
                output=self.surface,
                on_result=on_render_result,
                should_cancel=should_cancel_render
            )

            self.renderer.submit(request)

        self.render_thread = threading.Thread(target=render)
        self.render_thread.start()

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph: bpy.types.Depsgraph):
        print("UPDATE")
        self.tag_redraw()

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        if not self.needs_to_redraw:
            self.start_rendering(context, depsgraph)

        if self.needs_to_redraw:
            self.needs_to_redraw = False

            self.is_painting = True
            self.renderer.write_to(self.surface)
            
            scene = depsgraph.scene

            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE_MINUS_SRC_ALPHA)
            self.bind_display_space_shader(scene)
            
            tn.BlenderRenderEngine.draw(self.surface)
            
            self.unbind_display_space_shader()
            bgl.glDisable(bgl.GL_BLEND)

            self.is_painting = False

            if self.needs_to_redraw:
                self.tag_redraw()


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

