from src.ports.minio_port import MinioPort
from minio import Minio
import logging
import os
from dotenv import load_dotenv
from minio.error import S3Error
import uuid

# Configurar el logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MinioRepository(MinioPort):
    def __init__(self):
        logger.info("Inicializando MinioRepository")
        load_dotenv()
        minio_host = os.getenv("MINIO_HOST", "joyit_minio") 
        minio_port = os.getenv("MINIO_PORT", "6020")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "document-bucket")

        self.client = Minio(
            f"{minio_host}:{minio_port}",
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        
        if not self.client.bucket_exists(self.bucket_name):
            logger.debug(f"Bucket {self.bucket_name} no existe, creándolo")
            self.client.make_bucket(self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} creado exitosamente")
        else:
            logger.debug(f"Bucket {self.bucket_name} ya existe")

    def _generate_unique_filename(self, original_filename: str) -> tuple[str, str]:
        """
        Genera un nombre de archivo único usando UUID manteniendo la extensión original.
        Retorna una tupla con el UUID y el nombre completo del archivo.
        """
        file_extension = os.path.splitext(original_filename)[1]
        file_uuid = str(uuid.uuid4()) + file_extension  # Ahora incluye la extensión en el UUID
        new_filename = file_uuid  # El nuevo nombre completo es el UUID con extensión
        return file_uuid, new_filename

    def upload_file(self, file_path: str, file_name: str, bucket_name: str = None) -> str:
        try:
            if bucket_name is None:
                bucket_name = self.bucket_name 

            logger.debug(f"Iniciando carga de archivo: {file_path}")

            # Generar nuevo nombre con UUID
            file_uuid, new_filename = self._generate_unique_filename(file_name)
            logger.debug(f"Nombre generado con UUID: {new_filename}")

            # Subir archivo con el nuevo nombre
            self.client.fput_object(
                bucket_name,
                new_filename,
                file_path
            )
            logger.info(f"Archivo subido exitosamente como {new_filename} a {bucket_name}")

            # Generar la URL del archivo en MinIO usando solo el bucket y el nuevo nombre con extensión
            minio_host = os.getenv("MINIO_HOST")
            minio_port = os.getenv("MINIO_PORT")
            file_url = f"http://{minio_host}:{minio_port}/{bucket_name}/{new_filename}"  # Ajuste aquí
            logger.debug(f"URL generada: {file_url}")

            # Retornar solo la URL
            return file_url

        except Exception as e:
            logger.error(f"Error al subir archivo: {str(e)}")
            raise


    def check_file_minio(self, file_uuid: str) -> bool:
        try:
            # Usar el UUID directamente como nombre del archivo en MinIO
            file_name = file_uuid  # Ajusta esto si el formato es diferente.
            self.client.stat_object(self.bucket_name, file_name)
            logger.info(f"El archivo con UUID {file_uuid} existe en el bucket {self.bucket_name}.")
            return True
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                logger.warning(f"El archivo con UUID {file_uuid} no existe en el bucket {self.bucket_name}.")
                return False
            else:
                logger.error(f"Error al acceder al archivo con UUID {file_uuid}: {str(e)}")
                raise