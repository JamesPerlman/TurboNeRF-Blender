import bpy
import math

from turbo_nerf.blender_utility.driver_utility import force_update_drivers
from turbo_nerf.blender_utility.obj_type_utility import is_nerf_obj_type
from turbo_nerf.constants import OBJ_TYPE_NERF
from turbo_nerf.effects.spatial.repeater_effect import RepeaterEffect
from turbo_nerf.effects.utils.common import ALL_EFFECT_DESCRIPTORS, EFFECT_DESCRIPTORS_BY_ID, EFFECT_TYPES_BY_ID
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

class NeRFSpatialEffectListAddItemOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.spatial_effect_list_add_item"
    bl_label = "Add Effect"

    def execute(self, context):

        obj = context.object

        effects_list = obj.tn_nerf_spatial_effects_list

        ui_props = obj.tn_nerf_spatial_effects_panel_props

        effect_id = ui_props.spatial_effects_dropdown  # Set name to the selected option in the dropdown
        effect_descriptor = EFFECT_DESCRIPTORS_BY_ID[effect_id]
        effect_type = EFFECT_TYPES_BY_ID[effect_id]

        new_item = effects_list.add()
        new_item.effect_id = effect_id
        new_item.name = effect_descriptor.name

        effect_type.create_objects(context, obj)

        return {'FINISHED'}



class NeRFSpatialEffectListRemoveItemOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.spatial_effect_list_remove_item"
    bl_label = "Remove Effect"

    def execute(self, context):
        obj = context.object
        effects_list = obj.tn_nerf_spatial_effects_list
        selected_index = obj.tn_nerf_spatial_effects_list_index
        effects_list.remove(selected_index)
        obj.tn_nerf_spatial_effects_list_index = max(0, selected_index - 1)
        return {'FINISHED'}


class NeRFSpatialEffectListMoveItemToPrevOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.spatial_effect_list_move_item_to_prev"
    bl_label = "Move Effect Up"

    def execute(self, context):
        obj = context.object
        effects_list = obj.tn_nerf_spatial_effects_list
        selected_index = obj.tn_nerf_spatial_effects_list_index
        if selected_index > 0:
            effects_list.move(selected_index, selected_index - 1)
            obj.tn_nerf_spatial_effects_list_index = selected_index - 1
        return {'FINISHED'}
    

class NeRFSpatialEffectListMoveItemToNextOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.spatial_effect_list_move_item_to_next"
    bl_label = "Move Effect Down"

    def execute(self, context):
        obj = context.object
        effects_list = obj.tn_nerf_spatial_effects_list
        selected_index = obj.tn_nerf_spatial_effects_list_index
        if selected_index < len(effects_list) - 1:
            effects_list.move(selected_index, selected_index + 1)
            obj.tn_nerf_spatial_effects_list_index = selected_index + 1
        return {'FINISHED'}


class NeRFSpatialEffectItemProperties(bpy.types.PropertyGroup):
    effect_id: bpy.props.StringProperty(name="effect_id", default="")
    name: bpy.props.StringProperty(name="Name", default="Effect")
    repeater: bpy.props.PointerProperty(type=RepeaterEffect.descriptor().property_group_type)


class TN_UL_NeRFSpatialEffectsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # assume each item contains an id called name
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='OBJECT_DATAMODE')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OBJECT_DATAMODE')


class NeRFSpatialEffectsPanelProperties(bpy.types.PropertyGroup):

    spatial_effects_dropdown: bpy.props.EnumProperty(
        description="Spatial Effects",
        items=[(id, d.name, d.description) for id, d in EFFECT_DESCRIPTORS_BY_ID.items()]
    )


# Custom panel for the dropdown
class NeRFSpatialEffectsPanel(bpy.types.Panel):
    bl_label = "TurboNeRF Spatial Effects"
    bl_idname = "OBJECT_PT_turbo_nerf_spatial_effects_list_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    # poll
    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return is_nerf_obj_type(active_obj, OBJ_TYPE_NERF)
        

    def draw(self, context):
        layout = self.layout
        obj = context.object
        ui_props = obj.tn_nerf_spatial_effects_panel_props

        row = layout.row()
        row.label(text="Choose Effect: ")

        row = layout.row()
        row.prop(ui_props, "spatial_effects_dropdown", text="")
        row.operator(NeRFSpatialEffectListAddItemOperator.bl_idname, text="", icon="ADD")

        box = layout.box()
        row = box.row()
        col = row.column()
        col.template_list(
            listtype_name="TN_UL_NeRFSpatialEffectsList",
            list_id="tn_nerf_spatial_effects_list",
            dataptr=obj,
            propname="tn_nerf_spatial_effects_list",
            active_dataptr=obj,
            active_propname="tn_nerf_spatial_effects_list_index",
        )

        col = row.column(align=True)
        col.operator(NeRFSpatialEffectListMoveItemToPrevOperator.bl_idname, text="", icon="TRIA_UP")
        col.operator(NeRFSpatialEffectListMoveItemToNextOperator.bl_idname, text="", icon="TRIA_DOWN")
        col.separator()
        col.operator(NeRFSpatialEffectListRemoveItemOperator.bl_idname, text="", icon="REMOVE")

        # Draw UI for the selected effect
        if len(obj.tn_nerf_spatial_effects_list) == 0:
            return
        
        effect_props = obj.tn_nerf_spatial_effects_list[obj.tn_nerf_spatial_effects_list_index]
        
        if not effect_props.effect_id in EFFECT_TYPES_BY_ID:
            return
        
        effect = EFFECT_TYPES_BY_ID[effect_props.effect_id]
        
        nerf_obj = context.active_object
        
        box = layout.box()
        effect.draw_ui(effect_props, box, nerf_obj)

    # Register the custom property group and panel
    @classmethod
    def register(cls):
        bpy.utils.register_class(NeRFSpatialEffectListAddItemOperator)
        bpy.utils.register_class(NeRFSpatialEffectListRemoveItemOperator)
        bpy.utils.register_class(NeRFSpatialEffectListMoveItemToPrevOperator)
        bpy.utils.register_class(NeRFSpatialEffectListMoveItemToNextOperator)

        for type in [d.property_group_type for d in ALL_EFFECT_DESCRIPTORS]:
            bpy.utils.register_class(type)

        bpy.utils.register_class(TN_UL_NeRFSpatialEffectsList)
        bpy.utils.register_class(NeRFSpatialEffectItemProperties)
        bpy.utils.register_class(NeRFSpatialEffectsPanelProperties)
        
        bpy.types.Object.tn_nerf_spatial_effects_panel_props = bpy.props.PointerProperty(type=NeRFSpatialEffectsPanelProperties)
        bpy.types.Object.tn_nerf_spatial_effects_list = bpy.props.CollectionProperty(type=NeRFSpatialEffectItemProperties)
        bpy.types.Object.tn_nerf_spatial_effects_list_index = bpy.props.IntProperty(name="Index for spatial effects list", default=0)
        

    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(NeRFSpatialEffectListAddItemOperator)
        bpy.utils.unregister_class(NeRFSpatialEffectListRemoveItemOperator)
        bpy.utils.unregister_class(NeRFSpatialEffectListMoveItemToPrevOperator)
        bpy.utils.unregister_class(NeRFSpatialEffectListMoveItemToNextOperator)

        for type in [d.property_group_type for d in ALL_EFFECT_DESCRIPTORS]:
            bpy.utils.unregister_class(type)

        bpy.utils.unregister_class(TN_UL_NeRFSpatialEffectsList)
        bpy.utils.unregister_class(NeRFSpatialEffectItemProperties)
        bpy.utils.unregister_class(NeRFSpatialEffectsPanelProperties)

        del bpy.types.Object.tn_nerf_spatial_effects_panel_props
        del bpy.types.Object.tn_nerf_spatial_effects_list
        del bpy.types.Object.tn_nerf_spatial_effects_list_index

