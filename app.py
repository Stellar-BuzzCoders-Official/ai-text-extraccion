from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import base64
import tempfile
import logging
import json
import os
import yaml
import requests
import httpx
from minio.error import S3Error
from dotenv import load_dotenv

from src.services.image_services.image_to_text_service import ImageToTextService
from src.services.api_document_service import ApiDocumentService
from src.adapters.api_document_adapter.json_to_text_adapter import JsonAdapter
from src.adapters.api_document_adapter.yaml_to_text_adapter import YamlAdapter

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Document Processing API",
    description="API para procesamiento de documentos con soporte para múltiples formatos",
    version="2.0.0"
)

# Inicializar servicios
json_adapter = JsonAdapter()
yaml_adapter = YamlAdapter()
api_document_service = ApiDocumentService(json_adapter, yaml_adapter)
image_to_text_service = ImageToTextService()

# Configuración
api_storage_url = os.environ.get('API_STORAGE_URL', 'http://joyit-cn-ai-storage:5500/upload')
ALLOWED_TYPES = ['docx', 'pdf', 'jpg', 'png', 'jpeg', 'yaml', 'json']

# Modelos Pydantic para validación de datos
class SourceData(BaseModel):
    data: str = Field(..., description="Datos en formato base64")
    file_name: Optional[str] = Field(default=None, description="Nombre del archivo")
    name: Optional[str] = Field(default=None, description="Nombre alternativo del archivo")
    media_type: Optional[str] = Field(default=None, description="Tipo MIME del archivo")

class DocumentRequest(BaseModel):
    file_type: str = Field(..., description="Tipo de archivo", pattern="^(docx|pdf|jpg|png|jpeg|yaml|json)$")
    source: SourceData = Field(..., description="Datos fuente del documento")

class DocumentResponse(BaseModel):
    file_type: str
    file_url: str
    file_name: str
    file_size: int
    source: Dict[str, Any]

@app.get("/")
async def welcome():
    """Endpoint de bienvenida con información de la API"""
    logger.debug('Accediendo a la ruta principal')
    return {
        "message": "Bienvenido a la API de procesamiento de documentos",
        "tipos_soportados": ALLOWED_TYPES,
        "status": "active"
    }

@app.post("/process-file", response_model=DocumentResponse)
async def process_document(request: Request):
    """
    Procesa documentos desde datos base64
    
    Soporta tanto JSON como YAML en el body de la request
    """
    temp_file_name = None
    
    try:
        logger.debug('Iniciando procesamiento de documento')
        
        # Detectar y parsear el contenido según el Content-Type
        content_type = request.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            body = await request.json()
            data = DocumentRequest(**body)
        elif 'application/x-yaml' in content_type or 'text/yaml' in content_type:
            body_text = await request.body()
            yaml_data = yaml.safe_load(body_text.decode('utf-8'))
            data = DocumentRequest(**yaml_data)
        else:
            # Por defecto intentar JSON
            try:
                body = await request.json()
                data = DocumentRequest(**body)
            except Exception:
                logger.error('Formato de request no soportado')
                raise HTTPException(
                    status_code=415, 
                    detail="Formato de request no soportado. Use application/json o application/x-yaml"
                )

        logger.debug(f'Request recibido para tipo: {data.file_type}')

        # Obtener datos y configuración
        doc_type = data.file_type.lower()
        base64_data = data.source.data
        file_name = data.source.file_name or data.source.name or f'document.{doc_type}'
        
        if not base64_data:
            raise HTTPException(status_code=400, detail="Data en base64 es requerida")

        # Procesar y limpiar base64
        file_bytes = await _process_base64_data(base64_data, doc_type)
        
        # Crear archivo temporal
        temp_file_name = await _create_temp_file(file_bytes, doc_type)
        
        # Verificar el archivo temporal
        file_size = os.path.getsize(temp_file_name)
        logger.debug(f'Archivo temporal creado: {temp_file_name} con tamaño: {file_size} bytes')
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="El archivo temporal está vacío")

        # Procesar el documento según su tipo
        text_result = await _process_document_by_type(temp_file_name, doc_type)
        
        # Subir archivo a MinIO
        file_url = await _upload_to_minio(temp_file_name, file_name, doc_type)
        
        return DocumentResponse(
            file_type=doc_type,
            file_url=file_url,
            file_name=data.source.name or file_name,
            file_size=file_size,
            source={
                "type": "base64",
                "media_type": data.source.media_type or f'application/{doc_type}',
                "data": text_result,
                "status": "success"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error durante el procesamiento del documento: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error en el procesamiento del documento",
                "details": str(e)
            }
        )
    finally:
        # Limpiar archivo temporal
        if temp_file_name and os.path.exists(temp_file_name):
            try:
                os.remove(temp_file_name)
                logger.debug('Archivo temporal eliminado')
            except Exception as e:
                logger.warning(f'Error al eliminar archivo temporal: {str(e)}')

async def _process_base64_data(base64_data: str, doc_type: str) -> bytes:
    """Procesa y limpia los datos base64"""
    try:
        logger.debug(f'Longitud del base64 antes de la limpieza: {len(base64_data)}')
        base64_data = base64_data.strip()

        # Eliminar encabezados MIME
        mime_headers = {
            'pdf': 'data:application/pdf;base64,',
            'docx': 'data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,',
            'doc': 'data:application/msword;base64,',
            'json': 'data:application/json;base64,',
            'yaml': 'data:application/x-yaml;base64,',
            'jpg': 'data:image/jpeg;base64,',
            'jpeg': 'data:image/jpeg;base64,',
            'png': 'data:image/png;base64,'
        }

        if doc_type in mime_headers:
            base64_data = base64_data.replace(mime_headers[doc_type], '')

        # Limpiar caracteres no válidos
        valid_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
        base64_data = ''.join(c for c in base64_data if c in valid_chars)

        logger.debug(f'Longitud del base64 después de la limpieza: {len(base64_data)}')

        # Asegurar padding correcto
        padding_needed = len(base64_data) % 4
        if padding_needed:
            base64_data += '=' * (4 - padding_needed)

        # Decodificar
        file_bytes = base64.b64decode(base64_data)
        
        if len(file_bytes) == 0:
            raise ValueError("La decodificación resultó en 0 bytes")
            
        logger.debug(f'Decodificación de base64 exitosa. Tamaño: {len(file_bytes)} bytes')
        return file_bytes
        
    except Exception as e:
        logger.error(f'Error durante la decodificación de base64: {str(e)}')
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Error en la decodificación base64",
                "details": str(e),
                "data_length": len(base64_data) if base64_data else 0
            }
        )

async def _create_temp_file(file_bytes: bytes, doc_type: str) -> str:
    """Crea un archivo temporal con los datos proporcionados"""
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{doc_type}", delete=False) as temp_file:
            temp_file.write(file_bytes)
            return temp_file.name
    except Exception as e:
        logger.error(f'Error al crear archivo temporal: {str(e)}')
        raise HTTPException(status_code=500, detail=f"Error al crear archivo temporal: {str(e)}")

async def _process_document_by_type(temp_file_name: str, doc_type: str) -> str:
    """Procesa el documento según su tipo"""
    try:
        logger.debug(f'Procesando documento de tipo: {doc_type}')
        
        if doc_type in ['json', 'yaml']:
            # Leer archivo como texto
            with open(temp_file_name, 'r', encoding='utf-8') as file:
                file_content = file.read()
            
            logger.debug('Llamando al servicio de procesamiento de JSON/YAML')
            text_result = api_document_service.process_api_document(doc_type, file_content)
            logger.debug('Contenido extraído de JSON/YAML usando el servicio')
        else:
            logger.debug('Llamando al servicio de conversión de imagen a texto')
            text_result = image_to_text_service.convert_image_to_text(temp_file_name, doc_type)
            logger.debug('Conversión completada')
        
        return text_result
        
    except Exception as e:
        logger.error(f'Error al procesar documento: {str(e)}')
        raise HTTPException(status_code=500, detail=f"Error al procesar documento: {str(e)}")

async def _upload_to_minio(temp_file_name: str, file_name: str, doc_type: str) -> str:
    """Sube el archivo a MinIO y retorna la URL"""
    try:
        async with httpx.AsyncClient() as client:
            with open(temp_file_name, 'rb') as file:
                files = {'file': (file_name, file, f'application/{doc_type}')}
                data = {
                    'file_name': file_name,
                    'file_type': doc_type,
                    'bucket_name': "document-bucket"
                }
                
                response = await client.post(api_storage_url, files=files, data=data)
                
                if response.status_code != 200:
                    logger.error(f'Error al subir el archivo: {response.text}')
                    raise HTTPException(status_code=500, detail="Error al subir el archivo a MinIO")
                
                upload_data = response.json()
                file_url = upload_data.get('file_url')
                
                if not file_url:
                    raise HTTPException(status_code=500, detail="No se recibió URL del archivo subido")
                
                logger.debug(f'Documento subido exitosamente. URL: {file_url}')
                return file_url
                
    except httpx.HTTPError as e:
        logger.error(f'Error HTTP al subir archivo: {str(e)}')
        raise HTTPException(status_code=500, detail=f"Error de conexión al subir archivo: {str(e)}")
    except Exception as e:
        logger.error(f'Error inesperado al subir archivo: {str(e)}')
        raise HTTPException(status_code=500, detail=f"Error inesperado al subir archivo: {str(e)}")

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy", 
        "service": "document-processing-api",
        "supported_types": ALLOWED_TYPES
    }

if __name__ == '__main__':
    import uvicorn
    logger.info('Iniciando aplicación FastAPI')
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=7272,
        reload=True,
        log_level="debug"
    )