from src.adapters.minio_repository import MinioRepository
import logging

# Configurar el logger
logger = logging.getLogger(__name__)

class MinioService:
    def __init__(self):
        logger.info("Inicializando MinioService")
        self.minio_repository = MinioRepository()
    
    def upload_file(self, file_path: str, bucket_name: str) -> str:
        """
        Sube un archivo a MinIO usando el repositorio
        
        Args:
            file_path: Ruta del archivo a subir
            bucket_name: Nombre del bucket donde se subirá
            
        Returns:
            str: URL del archivo subido o None si hay error
        """
        logger.debug(f"Iniciando carga de archivo: {file_path} en bucket: {bucket_name}")
        result = self.minio_repository.upload_file(file_path, bucket_name)
        if result:
            logger.info(f"Archivo subido exitosamente. URL: {result}")
        else:
            logger.error("Error al subir el archivo")
        return result
    
    def check_file_minio(self, file_name: str) -> bool:
        """
        Verifica si un archivo existe en MinIO
        
        Args:
            file_name: Nombre del archivo a verificar
            
        Returns:
            bool: True si el archivo existe, False si no
        """
        logger.debug(f"Verificando si el archivo {file_name} existe en MinIO")
        return self.minio_repository.check_file_minio(file_name)