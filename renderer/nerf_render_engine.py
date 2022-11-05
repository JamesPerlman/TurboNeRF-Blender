from pathlib import Path
import bpy
import gpu
from gpu_extras.presets import draw_texture_2d
import numpy as np

import blender_nerf_tools.renderer.ngp_testbed_manager

from .ngp_testbed_manager import NGPTestbedManager

class InstantNeRFRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "INSTANT_NERF_RENDERER"
    bl_label = "Instant NeRF"
    bl_use_preview = True

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.scene_data = None
        self.draw_data = None

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        pass

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
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
                # convert camera matrix to z-axis up
                transform_matrix = np.matrix([
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ])
                camera_matrix *= transform_matrix

                NGPTestbedManager.set_camera_matrix(camera_matrix[:-1,:])
                print(f" set camera matrix {view_matrix}")

                # get region_3d's focal length

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        region = context.region
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height

        # Bind shader that converts from scene linear to display space,
        gpu.state.blend_set('ALPHA_PREMULT')
        self.bind_display_space_shader(scene)

        self.draw_data = CustomDrawData(dimensions)

        self.draw_data.draw()

        self.unbind_display_space_shader()
        gpu.state.blend_set('NONE')


class CustomDrawData:
    def __init__(self, dimensions):
        # Generate dummy float image buffer
        self.dimensions = dimensions
        width, height = dimensions
        pixels: gpu.types.Buffer
        if NGPTestbedManager.has_snapshot == True:
            pixels = np.flip(NGPTestbedManager.render(width, height), 0).flatten()
            pixels = gpu.types.Buffer('FLOAT', width * height * 4, pixels.tolist())
        else:
            pixels = gpu.types.Buffer('FLOAT', width * height * 4, width * height * [0.0, 0.0, 1.0, 1.0])
        
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

