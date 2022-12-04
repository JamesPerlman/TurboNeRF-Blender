import bpy

# dirty hack - re-evaluates drivers (thank you https://developer.blender.org/T74000)

def force_update_drivers(obj):
    obj.hide_render = obj.hide_render
    