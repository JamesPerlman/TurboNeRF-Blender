import bpy
from turbo_nerf.utility.nerf_manager import NeRFManager


class RemoveNeRFDatasetOperator(bpy.types.Operator):
    bl_idname = "nerf.remove_dataset"
    bl_label = "Remove NeRF Dataset"
    bl_description = "Remove the currently imported NeRF dataset"
    
    def execute(self, context):
        context.scene.nerf_dataset_panel_props.imported_dataset_path = ""
        
        # Select and delete all objects in the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        # Clear Recursive Datablocks 
        # This is so the file doesnt have unnecessary data attached to it. 
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        NeRFManager.items.clear()

        if NeRFManager.is_image_data_loaded():
            NeRFManager.unload_training_images()

        # bpy.context.area.tag_redraw()

        return {'FINISHED'}
