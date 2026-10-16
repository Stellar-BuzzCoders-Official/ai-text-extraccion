# src/services/document_service.py
from src.adapters.api_document_adapter import JsonAdapter
from src.adapters.api_document_adapter import YamlAdapter
import logging 

logger = logging.getLogger(__name__)

class ApiDocumentService:
    def __init__(self, json_adapter: JsonAdapter, yaml_adapter: YamlAdapter):
        self.json_adapter = json_adapter
        self.yaml_adapter = yaml_adapter

    def process_api_document(self, doc_type: str, data: str) -> str:
        logger.debug(f'Tipo de documento recibido: {doc_type}')
        if doc_type == 'json':
            logger.debug('Procesando como JSON...')
            return self.json_adapter.to_escaped_string(data)
        elif doc_type == 'yaml':
            logger.debug('Procesando como YAML...')
            return self.yaml_adapter.to_escaped_string(data)
        else:
            logger.error(f'Tipo de documento no soportado: {doc_type}')
            raise ValueError("Tipo de documento no soportado")
