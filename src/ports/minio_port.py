from abc import ABC, abstractmethod

class MinioPort(ABC):
    @abstractmethod
    def upload_file(self, file_path: str, bucket_name: str):
        pass
    @abstractmethod
    def check_file_minio(self, file_name: str) -> bool:
        pass