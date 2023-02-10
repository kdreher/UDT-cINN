from torch.utils.data import DataLoader
import pytorch_lightning as pl
from omegaconf import DictConfig
import json

from src.data.datasets.semantic_dataset import SemanticDataset
from src import settings
from src.utils.collate_function import collate_hsi


class SemanticDataModule(pl.LightningDataModule):
    def __init__(self, experiment_config: DictConfig, target='sampled'):
        """
        PyTorchLightning data loader. Each data loader feed the data as a dictionary containing the reflectances, the
        labels and a dictionary with mappings from labels (int) -> organ names (str).
        The shapes of the reflectances are `nr_samples * nr_channels` while the labels have a shape of
        `nr_samples`. Each data split was generated by splitting all pigs in the dataset such that each data split
        contains a unique set o f pigs and all organs are represented in each data split.
        By default, the test data set is hidden to avoind data leackage during training. During testing, it can be
        enabled through the context manager `EnableTestData`, and example of this is given below.

        >>> cfg = DictConfig(dict(shuffle=True, num_workers=2, batch_size=100, normalization="standardize"))
        >>> dm = SemanticDataModule(cfg)
        >>> dm.setup()
        >>> dl = dm.train_dataloader()
        >>> with EnableTestData(dm):
        >>>     test_dl = dm.test_dataloader()

        :param experiment_config: configuration containing loader parameters such as batch size, number of workers, etc.
            The minimum parameters expected are `shuffle, num_workers, batch_size, target`. The target should be `real`
            or `synthetic`. The target `real` represents the raw reflectances from different organs of pigs while the
            target `synthetic` represents simulated data that was generated by assigning the nearest neighbor to each
            pixel from real images.
        """
        super(SemanticDataModule, self).__init__()
        self.exp_config = experiment_config
        self.shuffle = experiment_config.shuffle
        self.num_workers = experiment_config.num_workers
        self.batch_size = experiment_config.batch_size
        self.train_dataset, self.val_dataset, self.test_dataset = None, None, None
        self.target = target
        self.dimensions = 100
        self.data_stats = self.load_data_stats()
        self.ignore_classes = ['gallbladder']
        self.organs = [o for o in settings.organ_labels if o not in self.ignore_classes]
        self.adjust_experiment_config()

    @staticmethod
    def load_data_stats():
        with open(str(settings.intermediates_dir / 'semantic' / 'data_stats.json'), 'rb') as handle:
            content = json.load(handle)
        return content

    def setup(self, stage: str) -> None:
        self.train_dataset = SemanticDataset(settings.intermediates_dir / 'semantic' / f'train_synthetic_{self.target}',
                                             settings.intermediates_dir / 'semantic' / f'train',
                                             exp_config=self.exp_config,
                                             ignore_classes=self.ignore_classes)
        self.val_dataset = SemanticDataset(settings.intermediates_dir / 'semantic' / f'val_synthetic_{self.target}',
                                           settings.intermediates_dir / 'semantic' / f'val',
                                           exp_config=self.exp_config,
                                           ignore_classes=self.ignore_classes)

    def train_dataloader(self) -> DataLoader:
        dl = DataLoader(self.train_dataset,
                        batch_size=self.batch_size,
                        shuffle=self.exp_config.shuffle,
                        num_workers=self.exp_config.num_workers,
                        pin_memory=True,
                        drop_last=True,
                        collate_fn=collate_hsi
                        )
        return dl

    def val_dataloader(self) -> DataLoader:
        dl = DataLoader(self.val_dataset,
                        batch_size=1,
                        shuffle=self.exp_config.shuffle,
                        num_workers=self.num_workers,
                        pin_memory=True,
                        drop_last=True,
                        collate_fn=collate_hsi
                        )
        return dl

    def test_dataloader(self) -> DataLoader:
        raise NotImplementedError

    def adjust_experiment_config(self):
        self.exp_config.data.dimensions = self.dimensions
        self.exp_config.data.mean_a = self.data_stats.get(f'train_synthetic_{self.target}').get('mean')
        self.exp_config.data.mean_b = self.data_stats.get(f'train').get('mean')
        self.exp_config.data.std_a = self.data_stats.get(f'train_synthetic_{self.target}').get('std')
        self.exp_config.data.std_b = self.data_stats.get(f'train').get('std')
        self.exp_config.data.n_classes = len(self.organs)


class EnableTestData:
    def __init__(self, dl: SemanticDataModule):
        self.dl = dl

    def __enter__(self):
        self.dl.test_dataset = SemanticDataset(settings.intermediates_dir / 'semantic' / f'test_synthetic_{self.dl.target}',
                                               settings.intermediates_dir / 'semantic' / f'test',
                                               exp_config=self.dl.exp_config,
                                               ignore_classes=self.dl.ignore_classes)

        def test_data_loader():
            dl = DataLoader(self.dl.test_dataset,
                            batch_size=self.dl.batch_size,
                            shuffle=self.dl.shuffle,
                            num_workers=self.dl.num_workers,
                            pin_memory=True,
                            drop_last=True,
                            collate_fn=collate_hsi
                            )
            return dl
        self.dl.__setattr__('test_dataloader', test_data_loader)
        return self.dl

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dl.__setattr__('test_dataloader', None)
