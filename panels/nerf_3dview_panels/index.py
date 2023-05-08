import bpy


from .dataset_panel import NeRF3DViewDatasetPanel
from .info_panel import NeRF3DViewInfoPanel
from .preview_panel import NeRF3DViewPreviewPanel
from .snapshot_panel import NeRF3DViewSnapshotPanel
from .training_panel import NeRF3DViewTrainingPanel

PANELS = [
    NeRF3DViewInfoPanel,
    # NeRF3DViewSnapshotPanel,
    NeRF3DViewDatasetPanel,
    NeRF3DViewTrainingPanel,
    NeRF3DViewPreviewPanel,
]


def register_nerf_3dview_panels():
    for panel in PANELS:
        bpy.utils.register_class(panel)
    

def unregister_nerf_3dview_panels():
    for panel in PANELS:
        bpy.utils.unregister_class(panel)

