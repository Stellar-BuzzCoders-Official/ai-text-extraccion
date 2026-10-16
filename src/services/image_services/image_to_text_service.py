import pytesseract
from PIL import Image
import logging
from src.services.image_services.to_image_service import ToImageService

# Configurar el logger
logger = logging.getLogger(__name__)

class ImageToTextService:
    def __init__(self):
        self.to_image_service = ToImageService()
        logger.info("ImageToTextService inicializado")

    def convert_image_to_text(self, file_path, file_type, lang='tesseract_es'):
        """
        Convierte imágenes a texto usando OCR de Tesseract.
        
        Args:
            file_path (str): Ruta al archivo a procesar.
            file_type (str): Tipo de archivo (e.g., 'pdf', 'docx').
            lang (str): Idioma para el OCR de Tesseract. Por defecto, español personalizado ('tesseract_es').
        
        Returns:
            str: Texto combinado extraído de las imágenes.
        """
        logger.debug(f"Iniciando conversión de {file_type} a texto desde {file_path}")
        
        # Convertir el documento a imágenes
        logger.debug("Convirtiendo documento a imágenes")
        images = self.to_image_service.convert_document_to_image(file_path, file_type)
        logger.debug(f"Se obtuvieron {len(images)} imágenes")
        
        # Extraer texto de cada imagen
        text_output = []
        for i, image in enumerate(images, 1):
            logger.debug(f"Procesando imagen {i} de {len(images)}")
            text = pytesseract.image_to_string(image, lang=lang)
            text_output.append(text)
            logger.debug(f"Texto extraído de la imagen {i}")
        
        logger.info("Conversión de imágenes a texto completada exitosamente")
        
        # Unir todos los textos extraídos en un único resultado
        combined_text = "\n".join(text_output)
        return combined_text
