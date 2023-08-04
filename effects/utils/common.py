
from turbo_nerf.effects.spatial.repeater_effect import RepeaterEffect

ALL_EFFECTS = [RepeaterEffect]
ALL_EFFECT_DESCRIPTORS = [effect.descriptor() for effect in ALL_EFFECTS]
EFFECT_DESCRIPTORS_BY_ID = { f"{i}": d for i, d in enumerate(ALL_EFFECT_DESCRIPTORS) }
EFFECT_TYPES_BY_ID = { f"{i}": e for i, e in enumerate(ALL_EFFECTS) }
