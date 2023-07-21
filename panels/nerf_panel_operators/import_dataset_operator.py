import bpy
from turbo_nerf.blender_utility.nerf_obj_utils import create_obj_for_nerf
from turbo_nerf.utility.nerf_manager import NeRFManager


class ImportNeRFDatasetOperator(bpy.types.Operator):
    """An Operator to import a NeRF dataset from a directory."""
    bl_idname = "turbo_nerf.import_dataset"
    bl_label = "Import Dataset"
    bl_description = "Import a dataset from a directory"

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print(f"Importing NeRF dataset from: {self.filepath}")

        nerf = NeRFManager.import_dataset(self.filepath)
        create_obj_for_nerf(context, nerf)

        return {'FINISHED'}

    def invoke(self, context, event):
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}


def menu_func_import(self, context):
    self.layout.operator(ImportNeRFDatasetOperator.bl_idname, text="NeRF Dataset")

def register():
    bpy.utils.register_class(ImportNeRFDatasetOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportNeRFDatasetOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
