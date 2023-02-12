from .dotdict import dotdict
from .pylib import PyTurboNeRF as tn

class NeRFManager():
    n_items = 0

    items = {}

    manager = None

    @classmethod
    def mgr(cls):
        if cls.manager is None:
            cls.manager = tn.Manager()
        
        return cls.manager
    
    @classmethod
    def create_trainable(cls, dataset_path):
        dataset = tn.Dataset(file_path=dataset_path)
        nerf = cls.mgr().create_trainable(bbox=dataset.bounding_box)

        item_id = cls.n_items
        item = dotdict({})
        item.dataset = dataset
        item.nerf = nerf

        cls.items[item_id] = item

        cls.n_items += 1

        return item_id

    @classmethod
    def train(cls, item_id, n_steps):
        item = cls.items[item_id]

        if not item.can_train:
            item.trainer = tn.Trainer(
                dataset=item.dataset,
                nerf=item.nerf,
                batch_size=2<<21
            )
            item.trainer.prepare_for_training()
            item.can_train = True
        
        while item.trainer.get_training_step() < n_steps:
            
            item.trainer.train_step()

            training_step = item.trainer.get_training_step()

            if training_step % 16 == 0 and training_step > 0:
                print(f"Step {training_step} of {n_steps} done")
                item.trainer.update_occupancy_grid(
                    selection_threshold=0.9,
                )