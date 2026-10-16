
from PIL import Image, ImageDraw
from src.ports.image_ports.ppt_to_image_port import PptToImagePort
import logging
import os

# Configurar el logger
logger = logging.getLogger(__name__)

class PptToImageAdapter(PptToImagePort):
    def __init__(self, file_path):
        self.file_path = file_path
        logger.info("PptToImageAdapter inicializado con la ruta del archivo")

    def convert_to_image(self):
        """"
        Convierte un archivo PPT a una imagen PNG
        """
        try:
            logger.info("Convirtiendo archivo PPT a imagen")
            # Cargar el archivo PPT
            image = Image.open(self.file_path)
            # Crear un objeto ImageDraw
            draw = ImageDraw.Draw(image)
            # Guardar la imagen
            image.save(os.path.splitext(self.file_path)[0] + ".png")
            logger.info("Archivo PPT convertido a imagen")
            return os.path.splitext(self.file_path)[0] + ".png"
        except Exception as e:
            logger.error(f"Error al convertir archivo PPT a imagen: {e}")
            return None
