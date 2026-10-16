import pytesseract
from PIL import Image
import logging
from src.ports.image_ports.image_to_text_port import ImageToTextPort

# Configurar el logger
logger = logging.getLogger(__name__)

class ImageToTextAdapter(ImageToTextPort):
    def __init__(self, file_path):
        self.file_path = file_path
        logger.info("ImageToTextAdapter inicializado con la ruta del archivo")

    def convert_image_to_text(self):
        logger.debug("Iniciando conversión de imagen a texto")
        try:
            # Abrir la imagen desde la ruta del archivo
            image = Image.open(self.file_path)
            logger.debug("Imagen cargada correctamente")
            
            text = pytesseract.image_to_string(image)
            logger.info("Conversión de imagen a texto completada exitosamente")
            return text
            
        except Exception as e:
            logger.error(f"Error durante la conversión: {str(e)}")
            return None
