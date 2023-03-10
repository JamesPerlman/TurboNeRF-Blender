import importlib
import bpy

# Thank you https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer

from turbo_nerf.operators.operator_export_nerfies_cameras import ExportNerfiesCameras
from turbo_nerf.operators.operator_export_world_matrix import ExportObjectWorldMatrix
from turbo_nerf.operators.operator_import_hypernerf_cams import ImportHyperNeRFCams
from turbo_nerf.operators.operator_import_nerf_transforms import ImportNeRFTransforms
from turbo_nerf.panels.render_panel_operators.camera_models.quadrilateral_hexahedron_camera import get_quadrilateral_hexahedron_camera_node_quaternion_rotation
from turbo_nerf.panels.render_panel_operators.camera_models.spherical_quadrilateral_camera import (
    get_spherical_quadrilateral_camera_node_location,
    get_spherical_quadrilateral_camera_node_quaternion_rotation,
)
from turbo_nerf.preferences.addon_preferences import (register_addon_preferences, unregister_addon_preferences)
from turbo_nerf.renderer.nerf_render_engine import (register_nerf_render_engine, unregister_nerf_render_engine)

# Definining the following import and export functions within the
# "Registration" class causes different errors when hovering over entries in
# "file/import" of the following form:
# "rna_uiItemO: operator missing srna 'import_scene.colmap_model'""

# Import/Export Functions

def _world_matrix_export_operator_function(topbar_file_export, context):
    topbar_file_export.layout.operator(
        ExportObjectWorldMatrix.bl_idname,
        text="World Matrix of Selected Object",
    )

def _nerfies_cameras_export_operator_function(topbar_file_export, context):
    topbar_file_export.layout.operator(
        ExportNerfiesCameras.bl_idname,
        text="Nerfies Cameras"
    )

def _nerf_transforms_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportNeRFTransforms.bl_idname,
        text="NeRF Transforms (JSON)"
    )

def _hypernerf_cams_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportHyperNeRFCams.bl_idname,
        text="HyperNeRF Cameras.json"
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
        cls._register_importer(
            ImportNeRFTransforms,
            _nerf_transforms_import_operator_function,
        )
        cls._register_importer(
            ImportHyperNeRFCams,
            _hypernerf_cams_import_operator_function,
        )

    @classmethod
    def unregister_importers(cls):
        """Unregister all registered importers."""
        cls._unregister_importer(
            ImportNeRFTransforms,
            _nerf_transforms_import_operator_function,
        )
        cls._unregister_importer(
            ImportHyperNeRFCams,
            _hypernerf_cams_import_operator_function,
        )

    @classmethod
    def register_exporters(cls):
        """Register exporters."""
        cls._register_exporter(
            ExportObjectWorldMatrix,
            _world_matrix_export_operator_function,
        )
        cls._register_exporter(
            ExportNerfiesCameras,
            _nerfies_cameras_export_operator_function,
        )

    @classmethod
    def unregister_exporters(cls):
        """Unregister all registered exporters."""
        cls._unregister_exporter(
            ExportObjectWorldMatrix,
            _world_matrix_export_operator_function
        )
        cls._unregister_exporter(
            ExportNerfiesCameras,
            _nerfies_cameras_export_operator_function,
        )
    
    @classmethod
    def register_drivers(cls):
        bpy.app.driver_namespace['get_spherical_quadrilateral_camera_node_location'] = get_spherical_quadrilateral_camera_node_location
        bpy.app.driver_namespace['get_spherical_quadrilateral_camera_node_quaternion_rotation'] = get_spherical_quadrilateral_camera_node_quaternion_rotation
        bpy.app.driver_namespace['get_quadrilateral_hexahedron_camera_node_quaternion_rotation'] = get_quadrilateral_hexahedron_camera_node_quaternion_rotation

    @classmethod
    def unregister_drivers(cls):
        del bpy.app.driver_namespace['get_spherical_quadrilateral_camera_node_location']
        del bpy.app.driver_namespace['get_spherical_quadrilateral_camera_node_quaternion_rotation']
        del bpy.app.driver_namespace['get_quadrilateral_hexahedron_camera_node_quaternion_rotation']

    @classmethod
    def register_misc_components(cls):
        register_nerf_render_engine()
        register_addon_preferences()

    @classmethod
    def unregister_misc_components(cls):
        unregister_nerf_render_engine()
        unregister_addon_preferences()

