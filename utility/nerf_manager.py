import bpy

from pathlib import Path

from turbo_nerf.constants import NERF_ITEM_IDENTIFIER_ID
from .dotdict import dotdict
from .pylib import PyTurboNeRF as tn

class NeRFManager():

    _bridge = None
    _manager = None
    _runtime_check_result = None

    @classmethod
    def pylib_version(cls):
        return tn.__version__
    
    @classmethod
    def required_pylib_version(cls):
        return "0.0.17"

    @classmethod
    def is_pylib_compatible(cls):
        return cls.pylib_version() == cls.required_pylib_version()
    
    @classmethod
    def check_runtime(cls):
        if cls._runtime_check_result is not None:
            return cls._runtime_check_result
        
        rm = tn.RuntimeManager()
        cls._runtime_check_result = rm.check_runtime()
        return cls._runtime_check_result

    @classmethod
    def bridge(cls):
        if cls._bridge is None:
            cls._bridge = tn.BlenderBridge()

        return cls._bridge

    @classmethod
    def import_dataset(cls, dataset_path):
        dataset = tn.Dataset(file_path=dataset_path)
        dataset.load_transforms()

        return cls.bridge().create_nerf(dataset)

    @classmethod
    def clone(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        cloned_nerf = cls.bridge().clone_nerf(nerf)
        return cloned_nerf.id
    
    @classmethod
    def destroy(cls, nerf_id: int):
        nerf = cls.get_nerf_by_id(nerf_id)
        cls.bridge().destroy_nerf(nerf)

    @classmethod
    def load_nerf(cls, path: Path):
        return cls.bridge().load_nerf(str(path.absolute()))

    @classmethod
    def save_nerf(cls, nerf_obj: bpy.types.Object, path: Path):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        cls.bridge().save_nerf(nerf, str(path.absolute()))

    @classmethod
    def get_all_nerfs(cls):
        return cls.bridge().get_nerfs()
    
    @classmethod
    def is_training(cls):
        return cls.bridge().is_training()

    @classmethod
    def get_training_step(cls):
        return cls.bridge().get_training_step()

    @classmethod
    def can_any_nerf_train(cls):
        return cls.bridge().can_any_nerf_train()

    @classmethod
    def can_nerf_obj_train(cls, nerf_obj: bpy.types.Object):
        if nerf_obj is None:
            return False
        
        nerf = cls.get_nerf_for_obj(nerf_obj)

        return nerf.can_train()

    @classmethod
    def is_image_data_loaded(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        return nerf.is_image_data_loaded()

    @classmethod
    def can_load_images(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        return cls.bridge().can_load_training_images(nerf)
    
    @classmethod
    def load_training_images(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        cls.bridge().load_training_images(nerf)
    
    @classmethod
    def start_training(cls):
        cls.bridge().start_training()
    
    @classmethod
    def stop_training(cls):
        cls.bridge().stop_training()

    @classmethod
    def unload_training_images(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        cls.bridge().unload_training_images(nerf)

    @classmethod
    def is_training_enabled(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        return cls.bridge().is_training_enabled(nerf)

    @classmethod
    def enable_training(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        cls.bridge().enable_training(nerf)
    
    @classmethod
    def disable_training(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        cls.bridge().disable_training(nerf)
    
    @classmethod
    def reset_training(cls, nerf_obj: bpy.types.Object):
        nerf = cls.get_nerf_for_obj(nerf_obj)
        cls.bridge().reset_training(nerf)

    @classmethod
    def toggle_training(cls):
        if cls.is_training():
            cls.stop_training()
        else:
            cls.start_training()
    
    @classmethod
    def get_nerf_by_id(cls, nerf_id: int) -> tn.NeRF:
        return cls.bridge().get_nerf(nerf_id)
    
    @classmethod
    def get_nerf_for_obj(cls, nerf_obj: bpy.types.Object) -> tn.NeRF:
        nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]
        return cls.get_nerf_by_id(nerf_id)
    
    @classmethod
    def get_trainer_for_nerf(cls, nerf: tn.NeRF) -> tn.Trainer:
        return cls.bridge().get_trainer_for_nerf(nerf)
    
    @classmethod
    def get_trainer_for_nerf_obj(cls, nerf_obj: bpy.types.Object) -> tn.Trainer:
        nerf = cls.get_nerf_for_obj(nerf_obj)
        return cls.get_trainer_for_nerf(nerf)
    
    @classmethod
    def set_bridge_object_property(cls, object_name, property_name, value):
        obj = getattr(cls.bridge(), object_name, None)
        if obj is None:
            return

        setattr(obj, property_name, value)
    
    @classmethod
    def get_bridge_object_property(cls, object_name, property_name, default=None):
        obj = getattr(cls.bridge(), object_name, None)
        if obj is None:
            return default

        return getattr(obj, property_name, default)
    
    @classmethod
    def bridge_obj_prop_setter(cls, obj_name, prop_name):
        def setter(self: bpy.types.PropertyGroup, value):
            cls.set_bridge_object_property(obj_name, prop_name, value)
        
        return setter
    
    @classmethod
    def bridge_obj_prop_getter(cls, obj_name, prop_name, default):
        def getter(self: bpy.types.PropertyGroup):
            return cls.get_bridge_object_property(obj_name, prop_name, default)
        
        return getter
