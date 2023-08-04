import bpy

from turbo_nerf.effects.utils.common import EFFECT_TYPES_BY_ID
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

def get_spatial_effects_for_nerf_obj(nerf_obj: bpy.types.Object) -> list[tn.SpatialEffect]:
    tn_effects: list[tn.SpatialEffect] = []

    for props in nerf_obj.tn_nerf_spatial_effects_list:
        effect_id = props.effect_id
        
        if effect_id not in EFFECT_TYPES_BY_ID:
            continue

        effect_type = EFFECT_TYPES_BY_ID[effect_id]
        
        tn_effect = effect_type.tn_instance(props, nerf_obj)
        tn_effects.append(tn_effect)
    
    return tn_effects
