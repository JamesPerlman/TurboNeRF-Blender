import bpy
from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj

from turbo_nerf.utility.nerf_manager import NeRFManager

class ExportNetworkSnapshotOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.export_network_snapshot"
    bl_label = "Export Snapshot"
    bl_options = {'REGISTER', 'UNDO'}

    # You can add properties here if needed, e.g.
    # file_path: bpy.props.StringProperty(name="File Path", default="//network_snapshot.json")
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".turbo"
    filter_glob: bpy.props.StringProperty(default='*.turbo', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return get_active_nerf_obj(context) is not None

    def execute(self, context):
        
        active_nerf_obj = get_active_nerf_obj(context)
        nerf = NeRFManager.get_nerf_for_obj(active_nerf_obj)
        NeRFManager

        self.save_network_snapshot(context)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        
        active_nerf_obj = get_active_nerf_obj(context)
        nerf = NeRFManager.get_nerf_for_obj(active_nerf_obj)
    
        self.filepath = f"snapshot-step-{nerf.training_step}.turbo"
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}
