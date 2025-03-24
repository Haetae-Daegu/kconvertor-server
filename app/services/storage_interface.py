from abc import ABC, abstractmethod
from typing import List


class StorageInterface(ABC):
    @abstractmethod
    def upload_files(self, files: List, folder: str) -> List[str]:
        pass

    @abstractmethod
    def delete_file(self, file_url: str) -> bool:
        pass
