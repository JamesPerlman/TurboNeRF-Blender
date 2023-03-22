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
        return "0.0.5"

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
        nerf = cls.mgr().create(bbox=dataset.bounding_box)

        item_id = cls.n_items
        item = dotdict({})
        item.dataset = dataset
        item.nerf = nerf

        cls.items[item_id] = item

        cls.n_items += 1

        return item_id
    
    @classmethod
    def is_training(cls):
        return cls.bridge().is_training()

    @classmethod
    def can_train(cls):
        # the condition here should be: if a nerf is currently selected
        # for now we just check if there are any nerfs
        return cls.n_items > 0

    @classmethod
    def can_import(cls):
        # this should not exist longterm
        return cls.n_items == 0
    
    @classmethod
    def start_training(cls):
        item = cls.items[0]
        cls.bridge().prepare_for_training(
            dataset=item.dataset,
            proxy=item.nerf,
            batch_size=2<<20
        )
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
