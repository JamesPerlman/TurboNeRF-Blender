import bpy
from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj
from turbo_nerf.blender_utility.object_utility import delete_object
from turbo_nerf.utility.nerf_manager import NeRFManager


class DeleteNeRFDatasetOperator(bpy.types.Operator):
    bl_label = "Delete NeRF Dataset"
    bl_idname = "turbo_nerf.delete_nerf_dataset_operator"
    bl_description = "Are you sure you want to delete?"
    bl_options = {'INTERNAL'}

    object_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        nerf_obj = get_active_nerf_obj(context)
        return nerf_obj is not None
        
    
    def execute(self, context):
    
        nerf_obj = get_active_nerf_obj(context)
        
        if NeRFManager.is_image_data_loaded(nerf_obj):
            NeRFManager.unload_training_images(nerf_obj)
            print("Unloaded Images")
            
        else: 
            print("No Images to Unload.")

        delete_object(nerf_obj)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="Are you sure you want to delete? This can't be undone.")

