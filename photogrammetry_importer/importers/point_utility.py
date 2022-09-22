import bpy
import numpy as np
from mathutils import Vector

from blender_nerf_tools.photogrammetry_importer.types.point import Point
from blender_nerf_tools.blender_utility.object_utility import (
    add_obj,
)
from blender_nerf_tools.photogrammetry_importer.utility.timing_utility import StopWatch
from blender_nerf_tools.blender_utility.logging_utility import log_report


def add_points_as_mesh_vertices(
    points,
    reconstruction_collection,
    add_mesh_to_point_geometry_nodes=True,
    point_radius=0.05,
    point_subdivisions=1,
    add_color_as_custom_property=True,
    op=None,
):
    """Add a point cloud as mesh."""
    log_report("INFO", "Adding Points as Mesh: ...", op)
    stop_watch = StopWatch()
    point_cloud_obj_name = "Mesh Point Cloud"
    point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
    point_cloud_mesh.update()
    point_cloud_mesh.validate()
    coords, colors = Point.split_points(points, normalize_colors=False)
    point_cloud_mesh.from_pydata(coords, [], [])
    point_cloud_obj = add_obj(
        point_cloud_mesh, point_cloud_obj_name, reconstruction_collection
    )
    if add_mesh_to_point_geometry_nodes:
        # Add a point_color attribute to each vertex
        point_cloud_mesh.attributes.new(
            name="point_color", type="FLOAT_COLOR", domain="POINT"
        )
        _add_colors_to_vertices(point_cloud_mesh, colors, "point_color")

        geometry_nodes = point_cloud_obj.modifiers.new(
            "GeometryNodes", "NODES"
        )
        # The group_input and the group_output nodes are created by default
        group_input = geometry_nodes.node_group.nodes["Group Input"]
        group_output = geometry_nodes.node_group.nodes["Group Output"]

        # Add modifier inputs that are editable from the GUI, the order these are added is important
        geometry_nodes.node_group.inputs.new(
            "NodeSocketMaterial", "Point Color"
        )  # Input_2
        geometry_nodes.node_group.inputs.new(
            "NodeSocketFloat", "Point Radius"
        )  # Input_3
        geometry_nodes.node_group.inputs.new(
            "NodeSocketIntUnsigned", "Point Subdivisions"
        )  # Input_4
        geometry_nodes["Input_2"] = _get_color_from_attribute("point_color")
        geometry_nodes["Input_3"] = point_radius
        geometry_nodes["Input_4"] = point_subdivisions

        # Note: To determine the name required for new(...), create the
        # corresponding node with the gui and print the value of "bl_rna".
        # Or enable python tooltips under preferences > interface and hover
        # over a node in the add node dropdown
        mesh_to_points = geometry_nodes.node_group.nodes.new(
            "GeometryNodeMeshToPoints"
        )
        instance_on_points = geometry_nodes.node_group.nodes.new(
            "GeometryNodeInstanceOnPoints"
        )
        realize_instances = geometry_nodes.node_group.nodes.new(
            "GeometryNodeRealizeInstances"
        )
        sphere_marker = geometry_nodes.node_group.nodes.new(
            "GeometryNodeMeshIcoSphere"
        )
        set_material = geometry_nodes.node_group.nodes.new(
            "GeometryNodeSetMaterial"
        )

        geometry_nodes.node_group.links.new(
            group_input.outputs["Geometry"], mesh_to_points.inputs["Mesh"]
        )
        geometry_nodes.node_group.links.new(
            mesh_to_points.outputs["Points"],
            instance_on_points.inputs["Points"],
        )
        geometry_nodes.node_group.links.new(
            instance_on_points.outputs["Instances"],
            realize_instances.inputs["Geometry"],
        )
        geometry_nodes.node_group.links.new(
            realize_instances.outputs["Geometry"],
            group_output.inputs["Geometry"],
        )

        geometry_nodes.node_group.links.new(
            group_input.outputs["Point Radius"], sphere_marker.inputs["Radius"]
        )
        geometry_nodes.node_group.links.new(
            group_input.outputs["Point Subdivisions"],
            sphere_marker.inputs["Subdivisions"],
        )
        geometry_nodes.node_group.links.new(
            sphere_marker.outputs["Mesh"], set_material.inputs["Geometry"]
        )
        geometry_nodes.node_group.links.new(
            group_input.outputs["Point Color"], set_material.inputs["Material"]
        )
        geometry_nodes.node_group.links.new(
            set_material.outputs["Geometry"],
            instance_on_points.inputs["Instance"],
        )

    if add_color_as_custom_property:
        point_cloud_obj["colors"] = colors

    log_report("INFO", "Duration: " + str(stop_watch.get_elapsed_time()), op)
    log_report("INFO", "Adding Points as Mesh: Done", op)
    return point_cloud_obj


def _add_colors_to_vertices(mesh, colors, attribute_name):
    """Add a color attribute to each vertex of mesh."""
    if len(mesh.vertices) != len(colors):
        raise ValueError(
            f"Got {len(mesh.vertices)} vertices and {len(colors)} color values."
        )

    color_array = np.array(colors)
    color_array[:, :3] /= 255.0
    mesh.attributes[attribute_name].data.foreach_set(
        "color", color_array.reshape(-1)
    )


def _get_color_from_attribute(attribute_name):
    """Create a material that obtains its color from the specified attribute."""
    material = bpy.data.materials.new("color")
    material.use_nodes = True
    color_node = material.node_tree.nodes.new("ShaderNodeAttribute")
    color_node.attribute_name = attribute_name
    material.node_tree.links.new(
        color_node.outputs["Color"],
        material.node_tree.nodes["Principled BSDF"].inputs["Base Color"],
    )
    return material
