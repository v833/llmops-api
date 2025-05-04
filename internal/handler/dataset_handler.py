from dataclasses import dataclass
from injector import inject


@inject
@dataclass
class DatasetHandler:
    def create_dataset(self, **kwargs):
        return "dataset"

    def get_dataset(self, **kwargs):
        return "dataset"

    def update_dataset(self, **kwargs):
        return "dataset"

    def embeddings_query(self, **kwargs):
        return "dataset"

    def get_datasets_with_page(self, **kwargs):
        return "dataset"
