from src.adapters.image_adapters.docx_to_image_adapter import DocxToImageAdapter
from src.adapters.image_adapters.pdf_to_image_adapter import PdfToImageAdapter
from src.adapters.image_adapters.pptx_to_image_adapter import PptxToImageAdapter
from src.adapters.image_adapters.doc_to_image_adapter import DocToImageAdapter
from src.adapters.image_adapters.ppt_to_image_adapter import PptToImageAdapter
import logging

# Configurar el logger
logger = logging.getLogger(__name__)

class ToImageService:
    def __init__(self):
        # El servicio está bien implementado ya que:
        # 1. Utiliza el patrón Adapter para manejar diferentes tipos de archivos
        # 2. Mantiene un diccionario de adaptadores que facilita la extensibilidad
        # 3. Encapsula la lógica de conversión para cada tipo de archivo
        logger.info("Inicializando ToImageService")
        self.adapters = {
            'docx': DocxToImageAdapter,
            'pdf': PdfToImageAdapter,
            'pptx': PptxToImageAdapter,
            'doc': DocToImageAdapter,
            'ppt': PptToImageAdapter,
        }
        logger.debug(f"Adaptadores registrados: {list(self.adapters.keys())}")

    def convert_document_to_image(self, file_path, file_type):
        logger.debug(f"Iniciando conversión de documento {file_path} de tipo {file_type}")
        # Obtiene el adaptador correcto basado en la extensión del archivo
        adapter_class = self.adapters.get(file_type.lower())
        if adapter_class:
            logger.debug(f"Usando adaptador: {adapter_class.__name__}")
            # Instancia el adaptador específico y realiza la conversión
            adapter = adapter_class(file_path)
            logger.info(f"Adaptador {adapter_class.__name__} inicializado correctamente")
            return adapter.convert_to_image()
        else:
            # Manejo de errores para tipos de archivo no soportados
            logger.error(f"Tipo de archivo no soportado: {file_type}")
            raise ValueError(f"Tipo de archivo no soportado: {file_type}")
