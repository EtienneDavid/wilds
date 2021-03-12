import numpy as np
import pandas as pd
import torch
from pathlib import Path
from PIL import Image
#from wilds.common.metrics.all_metrics import MultiTaskAccuracy
from wilds.datasets.wilds_dataset import WILDSDataset


class GWHDDataset(WILDSDataset):
    """
    The GWHD-wilds wheat head localization dataset.
    This is a modified version of the original Global Wheat Head Dataset.
    This dataset is not part of the official WILDS benchmark.
    We provide it for convenience and to reproduce observations discussed in the WILDS paper.

    Supported `split_scheme`:
        'official' for WILDS related tasks.
        To reproduce the baseline, several splits are needed:
        - to train a model on train domains and test against a all test split: 'train_in-dist'
        - to train a model on a portion of a specific val or test domain and test it against the remaining portion: 
        "{domain}_in-dist" where domain is the id of a domain (usask_1, uq_1, utokyo_1, utokyo_2, nau_1)

        no validation datasets are accessible for the baseline splits

    Input (x):
        1024x1024 RGB images of wheat field canopy between flowering and ripening.

    Output (y):
        y is a nx4-dimensional vector where each line represents a box coordinate (top-x,top-y,height,width)

    Metadata:
        Each image is annotated with the ID of the domain it came from (integer from 0 to 10).

    Website:
        http://www.global-wheat.com/

    Original publication:
        @article{david_global_2020,
            title = {Global {Wheat} {Head} {Detection} ({GWHD}) {Dataset}: {A} {Large} and {Diverse} {Dataset} of {High}-{Resolution} {RGB}-{Labelled} {Images} to {Develop} and {Benchmark} {Wheat} {Head} {Detection} {Methods}},
            volume = {2020},
            url = {https://doi.org/10.34133/2020/3521852},
            doi = {10.34133/2020/3521852},
            journal = {Plant Phenomics},
            author = {David, Etienne and Madec, Simon and Sadeghi-Tehran, Pouria and Aasen, Helge and Zheng, Bangyou and Liu, Shouyang and Kirchgessner, Norbert and Ishikawa, Goro and Nagasawa, Koichi and Badhon, Minhajul A. and Pozniak, Curtis and de Solan, Benoit and Hund, Andreas and Chapman, Scott C. and Baret, Frédéric and Stavness, Ian and Guo, Wei},
            month = aug,
            year = {2020},
            note = {Publisher: AAAS},
            pages = {3521852},
        }

    License:
        This dataset is distributed under the MIT license.
        https://github.com/snap-stanford/ogb/blob/master/LICENSE
    """

    def __init__(self, root_dir='data', download=False, split_scheme='official'):
        self._dataset_name = 'gwhd'
        self._version = '1.0'
        self._original_resolution = (1024, 1024)
        self._download_url = 'https://worksheets.codalab.org/rest/bundles/0x42fa9775eacc453489a428abd59a437d/contents/blob/'
        self._data_dir = self.initialize_data_dir(root_dir, download)
        self.root = Path(self.data_dir)

   
        self._split_scheme = split_scheme


        # Get filenames

        self._split_scheme = split_scheme


        if split_scheme =="official":
            train_data_df = pd.read_csv(self.root / f'{split_scheme}_train.csv')
            val_data_df = pd.read_csv(self.root / f'{split_scheme}_val.csv')
            test_data_df = pd.read_csv(self.root / f'{split_scheme}_test.csv')

        elif split_scheme == "train_in-dist":
            train_data_df = pd.read_csv(self.root / f'official_train.csv')
            test_data_df = pd.read_csv(self.root / f'{split_scheme}_test.csv')
            val_data_df = pd.DataFrame(columns=["image","labels","group"])
        elif split_scheme in [f"{domain}_in-dist" for domain in ["nau_1", "utokyo_1", "utokyo_2", "usask_1" , "uq_1"]]:
            train_data_df = pd.read_csv(self.root / f'{split_scheme}_train.csv')
            test_data_df = pd.read_csv(self.root / f'{split_scheme}_test.csv')
            val_data_df = pd.DataFrame(columns=["image","labels","group"])

        elif split_scheme == "in-dist":
            train_data_df = pd.read_csv(self.root / f'{split_scheme}_train.csv')
            test_data_df = pd.read_csv(self.root / f'{split_scheme}_test.csv')
            val_data_df = pd.DataFrame(columns=["image","labels","group"])
         

        self._image_array = []
        self._split_array, self._y_array, self._metadata_array = [], [], []

        for i, df in enumerate([train_data_df, val_data_df, test_data_df]):
            self._image_array.extend(list(df['image'].values))
            labels = list(df['labels'].values)
            self._split_array.extend([i] * len(labels))
            


            labels = [{"boxes": torch.stack([ torch.tensor([int(i) for i in box.split(" ")]) for box in boxes.split(";")]) ,"labels": torch.tensor([1.]*len(list(boxes.split(";")))).long() }  if type(boxes) != float else {"boxes":torch.empty(0,4),"labels":torch.empty(0,1,dtype=torch.long)} for boxes in labels]

            self._y_array.extend(labels)
            
            
            self._metadata_array.extend(list(df['group'].values))


        self._y_size = 1

        self._metadata_fields = ["domain"]

        self._split_array = np.array(self._split_array)
        
        
        
        
        self._metadata_array = torch.tensor(self._metadata_array,
                                            dtype=torch.long).unsqueeze(1)

        #self._metric = MultiTaskAccuracy()

    def get_input(self, idx):
       """
       Returns x for a given idx.
       """
       img_filename = self.root / "images" / self._image_array[idx]
       x = Image.open(img_filename)
       return x

    def eval(self, y_pred, y_true, metadata):
        return self.standard_group_eval(
            self._metric,
            self._eval_grouper,
            y_pred, y_true, metadata)
