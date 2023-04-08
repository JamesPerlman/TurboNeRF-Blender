from .dotdict import dotdict
from .pylib import PyTurboNeRF as tn

class NeRFManager():
    n_items = 0

    items = {}

    _bridge = None
    _manager = None

    @classmethod
    def pylib_version(cls):
        return tn.__version__
    
    @classmethod
    def required_pylib_version(cls):
        return "0.0.9"

    @classmethod
    def is_pylib_compatible(cls):
        return cls.pylib_version() == cls.required_pylib_version()

    @classmethod
    def mgr(cls):
        if cls._manager is None:
            cls._manager = tn.Manager()

        return cls._manager
    
    @classmethod
    def bridge(cls):
        if cls._bridge is None:
            cls._bridge = tn.BlenderBridge()

        return cls._bridge

    @classmethod
    def create_trainable(cls, dataset_path):
        dataset = tn.Dataset(file_path=dataset_path)

        nerf = cls.mgr().create(dataset)

        item_id = cls.n_items
        item = dotdict({})
        item.nerf = nerf

        cls.items[item_id] = item

        cls.n_items += 1

        return item_id
    
    @classmethod
    def is_training(cls):
        return cls.bridge().is_training()


    @classmethod
    def get_training_step(cls):
        return cls.bridge().get_training_step()

    @classmethod
    def is_ready_to_train(cls):
        return cls.bridge().is_ready_to_train()
    
    @classmethod
    def is_image_data_loaded(cls):
        return cls.bridge().is_image_data_loaded()
    
    @classmethod
    def can_load_images(cls):
        # TODO: need a better way to check if a dataset is loadable
        # return cls.bridge().can_load_images()

        return cls.n_items > 0 and not cls.is_image_data_loaded()

    @classmethod
    def can_import(cls):
        # this should not exist longterm
        return cls.n_items == 0
    
    @classmethod
    def prepare_for_training(cls, item_id):
        nerf = cls.items[item_id].nerf
        cls.bridge().prepare_for_training(
            proxy=nerf,
            batch_size=2<<20
        )

    @classmethod
    def start_training(cls):
        cls.bridge().start_training()
    
    @classmethod
    def stop_training(cls):
        cls.bridge().stop_training()

    @classmethod
    def toggle_training(cls):
        if cls.is_training():
            cls.stop_training()
        else:
            cls.start_training()
    
    @classmethod
    def reset_training(cls):
        cls.bridge().reset_training()
