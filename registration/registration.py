import importlib
import bpy

# Thank you https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer

from instant_ngp_tools.operators.operator_export_instant_ngp_transforms import (
    ExportInstantNGPTransforms,
)
from instant_ngp_tools.operators.operator_export_world_matrix import (
    ExportObjectWorldMatrix,
)

# Definining the following import and export functions within the
# "Registration" class causes different errors when hovering over entries in
# "file/import" of the following form:
# "rna_uiItemO: operator missing srna 'import_scene.colmap_model'""

# Import Functions
def _instant_ngp_transforms_export_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ExportInstantNGPTransforms.bl_idname, text="Instant-NGP Transforms for Rendering"
    )


def _world_matrix_export_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ExportObjectWorldMatrix.bl_idname,
        text="World Matrix of Selected Object",
    )

class Registration:
    """Class to register import and export operators."""

    # Define register/unregister Functions
    
    @classmethod
    def _register_importer(cls, importer, append_function):
        """Register a single importer."""
        bpy.utils.register_class(importer)
        bpy.types.TOPBAR_MT_file_import.append(append_function)

    @classmethod
    def _unregister_importer(cls, importer, append_function):
        """Unregister a single importer."""
        bpy.utils.unregister_class(importer)
        bpy.types.TOPBAR_MT_file_import.remove(append_function)

    @classmethod
    def _register_exporter(cls, exporter, append_function):
        """Register a single exporter."""
        bpy.utils.register_class(exporter)
        bpy.types.TOPBAR_MT_file_export.append(append_function)

    @classmethod
    def _unregister_exporter(cls, exporter, append_function):
        """Unregister a single exporter."""
        bpy.utils.unregister_class(exporter)
        bpy.types.TOPBAR_MT_file_export.remove(append_function)

    @classmethod
    def register_importers(cls):
        """Register importers."""
        # Nothing here yet
        pass

    @classmethod
    def unregister_importers(cls):
        """Unregister all registered importers."""
        # Nothing here yet
        pass

    @classmethod
    def register_exporters(cls):
        """Register exporters."""
        cls._register_exporter(
            ExportInstantNGPTransforms,
            _instant_ngp_transforms_export_operator_function,
        )
        cls._register_exporter(
            ExportObjectWorldMatrix,
            _world_matrix_export_operator_function,
        )

    @classmethod
    def unregister_exporters(cls):
        """Unregister all registered exporters."""
        cls._unregister_exporter(
            ExportInstantNGPTransforms,
            _instant_ngp_transforms_export_operator_function
        )
        cls._unregister_exporter(
            ExportObjectWorldMatrix,
            _world_matrix_export_operator_function
        )
