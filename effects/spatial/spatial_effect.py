import bpy

from abc import ABC, abstractmethod
from typing import Dict, Type

from turbo_nerf.utility import dotdict
from turbo_nerf.utility.pylib import PyTurboNeRF as tn

class SpatialEffectDescriptor():
    def __init__(self, name: str, description: str, property_group_type: bpy.types.PropertyGroup):
        self.name = name
        self.description = description
        self.property_group_type = property_group_type

class SpatialEffect(ABC):

    @classmethod
    @abstractmethod
    def tn_type(cls) -> Type[tn.SpatialEffect]:
        pass

    @classmethod
    @abstractmethod
    def descriptor(cls) -> SpatialEffectDescriptor:
        pass

    @classmethod
    @abstractmethod
    def create_objects(cls, context: bpy.types.Context, nerf_obj: bpy.types.Object):
        pass

    @classmethod
    @abstractmethod
    def destroy_objects(cls, context: bpy.types.Context, nerf_obj: bpy.types.Object):
        pass

    @classmethod
    @abstractmethod
    def draw_ui(cls, props: bpy.types.PropertyGroup, layout: bpy.types.UILayout, nerf_obj: bpy.types.Object):
        pass

    @classmethod
    @abstractmethod
    def get_tn_constructor_kwargs(cls, props: bpy.types.PropertyGroup, nerf_obj: bpy.types.Object) -> Dict[str, any]:
        pass

    @classmethod
    def tn_instance(cls, props: bpy.types.PropertyGroup, nerf_obj: bpy.types.Object) -> tn.SpatialEffect:
        return cls.tn_type()(**cls.get_tn_constructor_kwargs(props, nerf_obj))

