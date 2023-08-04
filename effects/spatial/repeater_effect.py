import bpy
import numpy as np

from typing import Dict, Type

from turbo_nerf.blender_utility.driver_utility import force_update_drivers, lock_prop_with_driver
from turbo_nerf.blender_utility.object_utility import add_cube
from turbo_nerf.effects.spatial.spatial_effect import SpatialEffect, SpatialEffectDescriptor
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

# look into class factories
class RepeaterEffectProperties(bpy.types.PropertyGroup):

    def update_drivers(self, context):
        # TODO: hardcode = badcode
        force_update_drivers(bpy.data.objects['SOURCE BBOX'])
        force_update_drivers(bpy.data.objects['EXTEND BBOX'])
    
    source_x: bpy.props.FloatVectorProperty(name="Source X", size=2, min=-128.0, max=128.0, step=0.01, precision=5, default=[-1.0, 1.0], update=update_drivers)
    source_y: bpy.props.FloatVectorProperty(name="Source Y", size=2, min=-128.0, max=128.0, step=0.01, precision=5, default=[-1.0, 1.0], update=update_drivers)
    source_z: bpy.props.FloatVectorProperty(name="Source Z", size=2, min=-128.0, max=128.0, step=0.01, precision=5, default=[-1.0, 1.0], update=update_drivers)

    extend_x: bpy.props.FloatVectorProperty(name="Extend X", size=2, step=0.01, precision=5, default=[-1.0, 1.0], update=update_drivers)
    extend_y: bpy.props.FloatVectorProperty(name="Extend Y", size=2, step=0.01, precision=5, default=[-1.0, 1.0], update=update_drivers)
    extend_z: bpy.props.FloatVectorProperty(name="Extend Z", size=2, step=0.01, precision=5, default=[-1.0, 1.0], update=update_drivers)
    

def add_linked_bbox(context: bpy.types.Context, parent: bpy.types.Object, name: str, propname_prefix: str) -> bpy.types.Object:
    bbox_obj = add_cube(name, size=1.0, collection=context.scene.collection)
    bbox_obj.display_type = "WIRE"
    bbox_obj.parent = parent

    bpy.ops.object.modifier_add(type='WIREFRAME')

    # drivers for linking scale & position to cropping
    locs = [fc.driver for fc in bbox_obj.driver_add('location')]
    scales = [fc.driver for fc in bbox_obj.driver_add('scale')]

    for i, dim in enumerate(['x', 'y', 'z']):
        # there has to be a better way.  maybe we can use getters & setters in the panel instead of drivers?
        locs[i].expression = f'(lambda v: (v[0] + v[1]) / 2)(get_spatial_effect_item_props("{parent.name}", 0).repeater.{propname_prefix}_{dim})'
        scales[i].expression = f'(lambda v: v[1] - v[0])(get_spatial_effect_item_props("{parent.name}", 0).repeater.{propname_prefix}_{dim})'

    
    # lock other transforms
    # TODO: we might actually want these to be usable
    lock_prop_with_driver(bbox_obj, 'rotation_euler', 0.0)
    lock_prop_with_driver(bbox_obj, 'rotation_mode', 1)

    return bbox_obj

class RepeaterEffect(SpatialEffect):
    @classmethod
    def tn_type(cls) -> Type[tn.SpatialEffect]:
        return tn.RepeaterEffect

    @classmethod
    def descriptor(cls) -> SpatialEffectDescriptor:
        return SpatialEffectDescriptor(
            name="Repeater",
            description="Modulo operator on the space",
            property_group_type=RepeaterEffectProperties
        )

    @classmethod
    def create_objects(cls, context: bpy.types.Context, nerf_obj: bpy.types.Object):
        add_linked_bbox(context, nerf_obj, "SOURCE BBOX", 'source')
        add_linked_bbox(context, nerf_obj, "EXTEND BBOX", 'extend')

    @classmethod
    def destroy_objects(cls, context: bpy.types.Context, nerf_obj: bpy.types.Object):
        pass

    @classmethod
    def draw_ui(cls, props: bpy.types.PropertyGroup, layout: bpy.types.UILayout, nerf_obj: bpy.types.Object):
        effect: RepeaterEffectProperties = props.repeater

        layout.label(text="Repeater Effect Properties")

        box = layout.box()

        for prop_name in ['source_x', 'source_y', 'source_z']:
            row = box.row()
            row.prop(effect, prop_name)
        
        box = layout.box()

        for prop_name in ['extend_x', 'extend_y', 'extend_z']:
            row = box.row()
            row.prop(effect, prop_name)
        

    @classmethod
    def get_tn_constructor_kwargs(cls, props: bpy.types.PropertyGroup, nerf_obj: bpy.types.Object) -> Dict[str, any]:
        source_bbox = tn.BoundingBox()

        source_bbox.min_x = props.repeater.source_x[0]
        source_bbox.max_x = props.repeater.source_x[1]
        
        source_bbox.min_y = props.repeater.source_y[0]
        source_bbox.max_y = props.repeater.source_y[1]

        source_bbox.min_z = props.repeater.source_z[0]
        source_bbox.max_z = props.repeater.source_z[1]

        extend_bbox = tn.BoundingBox()

        extend_bbox.min_x = props.repeater.extend_x[0]
        extend_bbox.max_x = props.repeater.extend_x[1]

        extend_bbox.min_y = props.repeater.extend_y[0]
        extend_bbox.max_y = props.repeater.extend_y[1]

        extend_bbox.min_z = props.repeater.extend_z[0]
        extend_bbox.max_z = props.repeater.extend_z[1]

        transform = tn.Transform4f(np.eye(4))

        return {
            'source_bbox': source_bbox,
            'extend_bbox': extend_bbox,
            'transform': transform
        }


