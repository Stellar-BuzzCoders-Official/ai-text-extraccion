from src.ports.image_ports.docx_to_image_port import DocxToImagePort
from PIL import Image, ImageDraw
import docx
import io
import logging

# Configurar el logger
logger = logging.getLogger(__name__)

class DocxToImageAdapter(DocxToImagePort):
    def __init__(self, doc_stream):
        self.doc_stream = doc_stream
        logger.info("DocToImageAdapter inicializado con el flujo del documento")

    def convert_to_image(self):
        logger.debug("Iniciando conversión de documento a imagen")
        try:
            # Abrir el documento desde el flujo
            doc = docx.Document(self.doc_stream)
            logger.info("Documento cargado correctamente")
            images = []
            
            for i, para in enumerate(doc.paragraphs):
                logger.debug(f"Procesando párrafo {i + 1}")
                
                # Crear una imagen nueva para cada párrafo
                img = Image.new('RGB', (500, 100), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                
                # Dibujar el texto del párrafo en la imagen
                d.text((10, 10), para.text, fill=(0, 0, 0))
                images.append(img)
                logger.debug(f"Imagen creada para párrafo {i + 1}")

            logger.info(f"Conversión completada. {len(images)} imágenes generadas")
            return images
            
        except Exception as e:
            logger.error(f"Error durante la conversión: {str(e)}")
            raise
