import fitz  # PyMuPDF
from PIL import Image
import logging
from src.ports.image_ports.pdf_to_image_port import PdfToImagePort

# Configurar el logger
logger = logging.getLogger(__name__)

class PdfToImageAdapter(PdfToImagePort):
    def __init__(self, file_path):
        self.file_path = file_path
        logger.info("PdfToImageAdapter inicializado con la ruta del archivo")

    def convert_to_image(self):
        logger.debug("Iniciando conversión de PDF a imagen")
        try:
            # Abrir el PDF desde la ruta del archivo
            pdf_document = fitz.open(self.file_path)
            logger.info("PDF cargado correctamente")
            images = []

            for page_number in range(len(pdf_document)):
                logger.debug(f"Procesando página {page_number + 1}")
                page = pdf_document.load_page(page_number)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
                logger.debug(f"Imagen creada para página {page_number + 1}")

            logger.info(f"Conversión completada. {len(images)} imágenes generadas")
            return images
            
        except Exception as e:
            logger.error(f"Error durante la conversión: {str(e)}")
            raise
