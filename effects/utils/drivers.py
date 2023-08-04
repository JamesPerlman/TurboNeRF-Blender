import bpy

def get_spatial_effect_item_props(obj_name: str, index: int):
    return bpy.data.objects[obj_name].tn_nerf_spatial_effects_list[index]