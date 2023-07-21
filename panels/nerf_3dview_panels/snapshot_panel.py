import bpy
from turbo_nerf.panels.nerf_panel_operators.export_nerf_snapshot_operator import ExportNetworkSnapshotOperator
from turbo_nerf.panels.nerf_panel_operators.import_nerf_snapshot_operator import ImportNetworkSnapshotOperator
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

class NeRF3DViewSnapshotPanel(bpy.types.Panel):
    """ NeRF Snapshot Management Panel Class """

    bl_label = "Snapshots"
    bl_idname = "VIEW3D_PT_turbo_nerf_snapshot_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TurboNeRF"

    observers = []


    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return NeRFManager.is_pylib_compatible()


    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""
        bpy.utils.register_class(ImportNetworkSnapshotOperator)
        bpy.utils.register_class(ExportNetworkSnapshotOperator)
        # cls.add_observers() cannot be added here (see draw())


    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ImportNetworkSnapshotOperator)
        bpy.utils.unregister_class(ExportNetworkSnapshotOperator)
        cls.remove_observers()


    @classmethod
    def remove_observers(cls):
        bridge = NeRFManager.bridge()
        for obid in cls.observers:
            bridge.remove_observer(obid)
        cls.observers.clear()

    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        layout = self.layout

        box = layout.box()
        box.label(text="Snapshots")

        row = box.row()
        row.operator(ImportNetworkSnapshotOperator.bl_idname, text="Load Snapshot")

        row = box.row()
        row.operator(ExportNetworkSnapshotOperator.bl_idname, text="Save Snapshot")


