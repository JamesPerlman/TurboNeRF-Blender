from instant_ngp_tools.blender_utility.logging_utility import log_report
from instant_ngp_tools.blender_utility.object_utility import (
    add_collection,
    add_cube,
    add_empty,
    get_collection,
    get_object
)

MAIN_COLLECTION = "Instant-NGP Tools"
GLOBAL_TRANSFORM = "GLOBAL_TRANSFORM"
AABB_BOX = "AABB_BOX"

AABB_MIN = "aabb_min"
AABB_MAX = "aabb_max"

class NGPScene:
    @classmethod
    def main_collection(cls):
        collection = get_collection(MAIN_COLLECTION)
        log_report('FUG', f"collection is {collection}")
        return collection
    
    @classmethod
    def create_main_collection(cls):
        collection = cls.main_collection()
        if collection is None:
            collection = add_collection(MAIN_COLLECTION)
        return collection

    @classmethod
    def global_transform(cls):
        return get_object(GLOBAL_TRANSFORM)
    
    @classmethod
    def create_global_transform(cls):
        obj = cls.global_transform()
        if obj is None:
            obj = add_empty(GLOBAL_TRANSFORM, cls.main_collection())
        else:
            cls.main_collection().objects.link(obj)
        return obj
    
    @classmethod
    def create_aabb_box(cls):
        obj = cls.aabb_box()
        if obj is None:
            obj = add_cube(AABB_BOX, cls.main_collection())
        else:
            cls.main_collection().objects.link(obj)
        return obj

    @classmethod
    def aabb_box(cls):
        return get_object(AABB_BOX)

    @classmethod
    def is_setup(cls):
        return (
            cls.main_collection() is not None
            and cls.aabb_box() is not None
            and cls.global_transform() is not None
        )
    
    @classmethod
    def get_aabb_min(cls):
        return cls.aabb_box()[AABB_MIN]
    
    @classmethod
    def set_aabb_min(cls, value):
        cls.aabb_box()[AABB_MIN] = value

    @classmethod
    def get_aabb_max(cls):
        return cls.aabb_box()[AABB_MAX]
    
    @classmethod
    def set_aabb_max(cls, value):
        cls.aabb_box()[AABB_MAX] = value
