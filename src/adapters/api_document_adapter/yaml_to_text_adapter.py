import json
import yaml
from src.ports.api_document_adapter.yaml_to_text_port import YamlPort   # noqa: F401
import logging

logger = logging.getLogger(__name__)

class YamlAdapter:
    def to_escaped_string(self, yaml_string: str) -> str:
        logger.debug('Convirtiendo YAML a string escapado...')
        try:
            # Cargar el contenido YAML
            yaml_data = yaml.safe_load(yaml_string)
            logger.debug('YAML cargado exitosamente')
            
            # Aquí puedes procesar los datos de YAML según tus necesidades
            # Por ejemplo, convertir a un string escapado:
            escaped_string = yaml.dump(yaml_data)
            logger.debug('YAML convertido a string escapado')
            return escaped_string
        except Exception as e:
            logger.error(f'Error al procesar el YAML: {str(e)}')
            raise ValueError("Error al procesar el documento YAML")