import bpy
import bmesh

from blender_nerf_tools.blender_utility.logging_utility import log_report


def add_empty(name, collection=None, type='PLAIN_AXES'):
    """Add an empty to the scene."""
    if collection is None:
        collection = bpy.context.collection
    empty_obj = bpy.data.objects.new(name, None)
    empty_obj.empty_display_type = type
    collection.objects.link(empty_obj)
    return empty_obj


def add_cube(cube_name, collection=None):
    """Add a cube to the scene."""
    if collection is None:
        collection = bpy.context.collection

    mesh = bpy.data.meshes.new('Cube')
    cube = bpy.data.objects.new(cube_name, mesh)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()

    collection.objects.link(cube)

    return cube

def add_obj(data, obj_name, collection=None):
    """Add an object to the scene."""
    if collection is None:
        collection = bpy.context.collection

    new_obj = bpy.data.objects.new(obj_name, data)
    collection.objects.link(new_obj)
    new_obj.select_set(state=True)

    if (
        bpy.context.view_layer.objects.active is None
        or bpy.context.view_layer.objects.active.mode == "OBJECT"
    ):
        bpy.context.view_layer.objects.active = new_obj
    return new_obj

def get_selected_empty():
    """Get the selected empty or return None."""
    selected_obj = get_selected_object()
    if selected_obj is None:
        return None
    elif selected_obj.type == "EMPTY":
        return selected_obj
    else:
        return None


def get_selected_object():
    """Get the selected object or return None."""
    selection_names = [obj.name for obj in bpy.context.selected_objects]
    if len(selection_names) == 0:
        return None
    selected_obj = bpy.data.objects[selection_names[0]]
    return selected_obj


def get_object(object_name):
    """Returns the first object matching object_name."""
    
    objects = bpy.context.scene.objects
    if str(object_name) in objects:
        return objects[object_name]
    
    return None


def add_collection(collection_name, parent_collection=None):
    """Add a collection to the scene."""
    if parent_collection is None:
        parent_collection = bpy.context.scene.collection

    new_collection = bpy.data.collections.new(collection_name)
    parent_collection.children.link(new_collection)

    return new_collection


def get_collection(collection_name):
    """Returns the first collection that matches the given name."""
    if str(collection_name) in bpy.data.collections:
        return bpy.data.collections[collection_name]

    return None

