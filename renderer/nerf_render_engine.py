from pathlib import Path
import bpy
import gpu
from gpu_extras.presets import draw_texture_2d
import numpy as np
import time
from threading import Thread

from blender_nerf_tools.blender_utility.nerf_render_manager import NeRFRenderManager
from .ngp_testbed_manager import NGPTestbedManager
import copy

# TODO: this is a util
# thank you https://stackoverflow.com/a/58567022/892990
#simple image scaling to (nR x nC) size
def scale(im, nR, nC):
    nR0 = im.shape[0]     # source number of rows 
    nC0 = im.shape[1]  # source number of columns 
    if nR0 == nR and nC0 == nC:
        return im

    return np.array([
        [im[int(nR0 * r / nR)][int(nC0 * c / nC)] for c in range(nC)]
        for r in range(nR)
    ])

MAX_MIP_LEVEL = 4
class InstantNeRFRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "INSTANT_NERF_RENDERER"
    bl_label = "Instant NeRF"
    bl_use_eevee_viewport = True
    bl_use_preview = True
    bl_use_exclude_layers = True
    bl_use_custom_freestyle = True

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.scene_data = None
        self.draw_data = None
        self.latest_render_result = None
        self.needs_to_redraw = False
        self.user_updated_scene = False

        self.prev_view_dimensions = np.array([0, 0])
        self.prev_region_camera_matrix = np.eye(4)
        self.mip_level = MAX_MIP_LEVEL

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        pass

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        print("render")
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)

        # Fill the render result with a flat color. The framebuffer is
        # defined as a list of pixels, each pixel itself being a list of
        # R,G,B,A values.
        if self.is_preview:
            color = [0.1, 0.7, 0.5, 1.0]
        else:
            color = [0.7, 0.4, 0.1, 1.0]

        pixel_count = self.size_x * self.size_y
        rect = [color] * pixel_count

        # Here we write the pixel values to the RenderResult
        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0].passes["Combined"]
        layer.rect = rect
        self.end_result(result)

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph: bpy.types.Depsgraph):
        print("view_update")
        region = context.region
        view3d = context.space_data
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height

        if not self.scene_data:
            # First time initialization
            self.scene_data = []
            first_time = True

            # Loop over all datablocks used in the scene.
            for datablock in depsgraph.ids:
                pass
        else:
            first_time = False

            # Test which datablocks changed
            for update in depsgraph.updates:
                print("Datablock updated: ", update.id.name)

            # Test if any material was added, removed or changed.
            if depsgraph.id_type_updated('MATERIAL'):
                print("Materials updated")

        # Loop over all object instances in the scene.
        if first_time or depsgraph.id_type_updated('OBJECT'):
            #print(f"{dir(depsgraph)}")
            #print(f"{depsgraph.objects}")
            for obj in depsgraph.objects:
                if "prop" in obj:
                    print(obj["prop"])
            for instance in depsgraph.object_instances:
                instance: bpy.types.DepsgraphObjectInstance
                #print(f"{dir(instance)}")
                pass
        
        for area in context.screen.areas:
            area: bpy.types.Area
            if area.type == 'VIEW_3D':
                region_3d: bpy.types.RegionView3D = area.spaces.active.region_3d
                # P
                projection_matrix = region_3d.window_matrix
                # V 
                view_matrix = region_3d.view_matrix
                # P * V
                view_projection_matrix = region_3d.perspective_matrix

                # need to pass this into ngp
                camera_matrix = np.matrix([list(r) for r in context.scene.camera.matrix_world])
                NGPTestbedManager.set_camera_matrix(camera_matrix[:-1,:])

                # get region_3d's focal length
        # make sure to set this
        self.user_updated_scene = True
    

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        print("view_draw")
        region = context.region
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height

        # TODO: abstract this
        def draw_latest_render_result():
            if self.latest_render_result is not None:
                gpu.state.blend_set('ALPHA_PREMULT')
                self.bind_display_space_shader(scene)

                result = self.latest_render_result # scale(self.latest_render_result, region.width, region.height)
                
                self.draw_data = CustomDrawData(result, result.shape[1], result.shape[0])

                self.draw_data.draw()

                self.unbind_display_space_shader()
                gpu.state.blend_set('NONE')
        
        
        def save_render_result(result: list):
            self.latest_render_result = result
            self.needs_to_redraw = True
            self.is_rendering = False
            self.tag_redraw()
        
        # First we must determine if the user initiated this view_draw
        # To do this, we will check if the dimensions or the camera matrix has changed
       
        # TODO: abstract this
        def get_region_camera_matrices():
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    region_3d: bpy.types.RegionView3D = area.spaces.active.region_3d
                    # P
                    projection_matrix = np.array(region_3d.window_matrix)
                    # V 
                    view_matrix = np.array(region_3d.view_matrix)
                    # P * V
                    perspective_matrix = np.array(region_3d.perspective_matrix)

                    return (projection_matrix, view_matrix, perspective_matrix)
            
            return (np.eye(4), np.eye(4), np.eye(4))
        
        (projection_matrix, view_matrix, perspective_matrix) = get_region_camera_matrices()
        
        dims_array = np.array([region.width, region.height])
        updated_region_size = not np.array_equal(self.prev_view_dimensions, dims_array)
        updated_region_view = not np.array_equal(self.prev_region_camera_matrix, perspective_matrix)
        user_initiated_view_draw = updated_region_size or updated_region_view or self.user_updated_scene
        if user_initiated_view_draw:
            print("USER INITIATED!")
            self.user_updated_scene = False
            self.prev_view_dimensions = copy.copy(dims_array)
            self.prev_region_camera_matrix = copy.copy(perspective_matrix)

            # reset mip level
            self.mip_level = MAX_MIP_LEVEL

            # start a render chain
            view_matrix = np.array(context.scene.camera.matrix_world)
            NGPTestbedManager.set_camera_matrix(view_matrix[:-1,:])
            # TODO: set focal length, masks

            # TODO: cancel previous render, or queue up next render.  request_nerf_render will not work if it is currently already rendering

            

            self.needs_to_redraw = False
            self.is_rendering = True
            NGPTestbedManager.request_render(region.width, region.height, self.mip_level, save_render_result)

            draw_latest_render_result()
            return

        # user did NOT initiate this view_draw
        draw_latest_render_result()
        
        if self.needs_to_redraw:
            print(f"NEEDS TO REDRAW!")
            self.needs_to_redraw = False

            # kick off a new render at the next mip level
            if self.mip_level > 1:
                self.mip_level -= 1
                # start a render chain
                
                view_matrix = np.array(context.scene.camera.matrix_world)
                NGPTestbedManager.set_camera_matrix(view_matrix[:-1,:])
                # TODO: set focal length, masks
                self.is_rendering = True
                NGPTestbedManager.request_render(region.width, region.height, self.mip_level, save_render_result)


        
   
    
    def update(self, data: bpy.types.BlendData, depsgraph: bpy.types.Depsgraph):
        print("update()")

    def draw(self, context: bpy.types.Context, depsgraph: bpy.types.Depsgraph):
        print("draw()")
    
    def tag_redraw(self):
        print("tag_redraw()")
    
    def tag_update(self):
        print("tag_update()")


class CustomDrawData:
    def __init__(self, render_data, width, height):
        # Generate dummy float image buffer
        self.dimensions = (width, height)
        # pixels = np.flip(render_data, 0).flatten()
        pixels = gpu.types.Buffer('FLOAT', width * height * 4, render_data)

        # Generate texture
        self.texture = gpu.types.GPUTexture((width, height), format='RGBA16F', data=pixels)

        # Note: This is just a didactic example.
        # In this case it would be more convenient to fill the texture with:

    def __del__(self):
        del self.texture

    def draw(self):
        draw_texture_2d(self.texture, (0, 0), self.texture.width, self.texture.height)


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
    bpy.utils.register_class(InstantNeRFRenderEngine)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('INSTANT_NERF_RENDERER')


def unregister_nerf_render_engine():
    bpy.utils.unregister_class(InstantNeRFRenderEngine)

    for panel in get_panels():
        if 'CUSTOM' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('INSTANT_NERF_RENDERER')

