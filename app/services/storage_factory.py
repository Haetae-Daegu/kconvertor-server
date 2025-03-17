from enum import Enum
from app.services.storage_interface import StorageInterface
from app.services.s3_service import S3Service


class StorageType(Enum):
    S3 = "s3"


class StorageFactory:
    @staticmethod
    def get_storage_service(storage_type: StorageType) -> StorageInterface:
        if storage_type == StorageType.S3:
            return S3Service()
