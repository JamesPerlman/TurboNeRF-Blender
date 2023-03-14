from .dotdict import dotdict
from .pylib import PyTurboNeRF as tn
from threading import Thread

# TODO: move this somewhere else? make it a range? this code seems smelly
class NeRFManager():
    n_items = 0

    items = {}

    _bridge = None
    _manager = None

    training_thread = None
    
    @classmethod
    def pylib_version(cls):
        return tn.__version__
    
    @classmethod
    def required_pylib_version(cls):
        return "0.0.1"

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

    # @classmethod
    # def train_async(cls, item_id, n_steps):
    #     if cls.training_thread is not None:
    #         return
        
    #     def on_finish():
    #         cls.training_thread = None
        
    #     cls.training_thread = Thread(
    #         target=cls.train,
    #         args=(item_id, n_steps, on_finish)
    #     )

    #     cls.training_thread.start()

    # @classmethod
    # def train(cls, item_id, n_steps, callback=None):
    #     item = cls.items[item_id]

    #     if not item.can_train:
            
    #         item.can_train = True

    #     cur_step = item.trainer.get_training_step()
    #     total_steps = cur_step + n_steps
        
    #     while item.trainer.get_training_step() < total_steps:
            
    #         item.trainer.train_step()

    #         training_step = item.trainer.get_training_step()

    #         if training_step % 16 == 0 and training_step > 0:
    #             print(f"Step {training_step} of {n_steps} done")
    #             item.trainer.update_occupancy_grid(
    #                 selection_threshold=0.9,
    #             )
    
    #     if callback is not None:
    #         callback()
