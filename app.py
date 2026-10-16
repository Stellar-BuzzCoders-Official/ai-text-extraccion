from flask import Flask, request, jsonify
from src.services.image_services.image_to_text_service import ImageToTextService
from src.services.api_document_service import ApiDocumentService
from src.adapters.api_document_adapter.json_to_text_adapter import JsonAdapter
from src.adapters.api_document_adapter.yaml_to_text_adapter import YamlAdapter
import base64
import tempfile
import logging
import json
import os
import yaml
import requests
from minio.error import S3Error
from dotenv import load_dotenv

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Subir el documento a MinIO y obtener la URL
json_adapter = JsonAdapter()
yaml_adapter = YamlAdapter()
api_document_service = ApiDocumentService(json_adapter, yaml_adapter)
logger.debug('Iniciando conversión de imagen a texto')
image_to_text_service = ImageToTextService()
api_storage_url = os.environ.get('API_STORAGE_URL', 'http://joyit-cn-ai-storage:5500/upload')

ALLOWED_TYPES = ['docx', 'pdf', 'jpg', 'png', 'jpeg', 'yaml', 'json']

@app.route('/', methods=['GET'])
def welcome():
    logger.debug('Accediendo a la ruta principal')
    return jsonify({
        "message": "Bienvenido a la API de procesamiento de documentos",
        "tipos_soportados": ALLOWED_TYPES,
        "status": "active",
    }), 200
    
@app.route('/process-file', methods=['POST'])
def process_document():
    try:
        logger.debug('Iniciando procesamiento de documento')
        
        # Detectar si la entrada es JSON o YAML
        if request.content_type == 'application/json':
            data = request.get_json()
        elif request.content_type == 'application/x-yaml':
            data = request.get_data(as_text=True)  # Obtener los datos como texto
        else:
            logger.error('Formato de request no soportado')
            return jsonify({"error": "Formato de request no soportado"}), 415

        logger.debug(f'Request recibido: {data}')

        # Validación de la estructura del request
        if not data or 'file_type' not in data or 'source' not in data:
            logger.error('Formato de request inválido')
            return jsonify({"error": "Formato de request inválido"}), 400

        # Obtener y validar el tipo de documento
        doc_type = data['file_type'].lower()
        logger.debug(f'Tipo de documento: {doc_type}')
        
        # Validar tipo de documento
        if doc_type not in ALLOWED_TYPES:
            logger.error(f'Tipo de documento no soportado: {doc_type}')
            return jsonify({"error": f"Tipo de documento no soportado. Tipos permitidos: {ALLOWED_TYPES}"}), 400

        # Obtener y validar el base64
        base64_data = data['source'].get('data')
        if not base64_data:
            logger.error('Data en base64 no proporcionada')
            return jsonify({"error": "Data en base64 es requerida"}), 400

        # Limpieza y validación mejorada del base64
        logger.debug(f'Longitud del base64 antes de la limpieza: {len(base64_data)}')
        try:
            base64_data = base64_data.strip()

            # Eliminar encabezados MIME
            mime_headers = {
                'pdf': 'data:application/pdf;base64,',
                'docx': 'data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,',
                'doc': 'data:application/msword;base64,',
                'json': 'data:application/json;base64,',
                'yaml': 'data:application/x-yaml;base64,'  
            }

            if doc_type in mime_headers:
                base64_data = base64_data.replace(mime_headers[doc_type], '')

            valid_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
            base64_data = ''.join(c for c in base64_data if c in valid_chars)

            logger.debug(f'Longitud del base64 después de la limpieza: {len(base64_data)}')

            # Asegurar que la longitud sea múltiplo de 4
            padding_needed = len(base64_data) % 4
            if padding_needed:
                base64_data += '=' * (4 - padding_needed)

            # Intentar decodificar
            file_bytes = base64.b64decode(base64_data)

            # Verificar que tenemos datos válidos
            if len(file_bytes) == 0:
                raise ValueError("La decodificación resultó en 0 bytes")
            logger.debug(f'Decodificación de base64 exitosa. Tamaño: {len(file_bytes)} bytes')

            # Crear un archivo temporal con manejo de contexto
            logger.debug('Convirtiendo base64 a archivo temporal')
            file_name = data['source'].get('file_name', f'document.{doc_type}')

            # Crear un archivo temporal
            with tempfile.NamedTemporaryFile(suffix=f".{doc_type}", delete=False) as temp_file:
                temp_file.write(file_bytes)
                temp_file_name = temp_file.name

            # Verificar el tamaño del archivo temporal
            file_size = os.path.getsize(temp_file_name)
            logger.debug(f'Archivo temporal creado: {temp_file_name} con tamaño: {file_size} bytes')

            if file_size == 0:
                raise ValueError("El archivo temporal está vacío")

            logger.info(f'Procesando archivo temporal: {temp_file_name}')

            # Leer el contenido del archivo temporal en modo texto o binario según el tipo
            if doc_type in ['json', 'yaml']:
                with open(temp_file_name, 'r', encoding='utf-8') as file:
                    file_content = file.read()
            else:
                with open(temp_file_name, 'rb') as file:
                    file_content = file.read()  

            # Procesar el documento según su tipo
            logger.debug(f'Procesando documento de tipo: {doc_type}')
            match doc_type:
                case 'json' | 'yaml':
                    logger.debug('Llamando al servicio de procesamiento de JSON/YAML')
                    text_result = api_document_service.process_api_document(doc_type, file_content)
                    logger.debug('Contenido extraído de JSON/YAML usando el servicio')
                case _:
                    logger.debug('Llamando al servicio de conversión de imagen a texto')
                    text_result = image_to_text_service.convert_image_to_text(temp_file_name, doc_type)
                    logger.debug('Conversión completada')

            # Subir el archivo a MinIO
            
            files = {'file': open(temp_file_name, 'rb')}
            payload = {
                'file_name': file_name,
                'file_type': doc_type,
                'bucket_name': "document-bucket"
            }

            # Realizamos la petición POST para cargar el archivo
            upload_response = requests.post(api_storage_url, files=files, data=payload)
            
            # Verificar si la carga fue exitosa
            if upload_response.status_code != 200:
                logger.error(f'Error al subir el archivo: {upload_response.json()}')
                return jsonify({"error": "Error al subir el archivo a MinIO"}), 500

            # Obtener la URL del archivo subido
            file_url = upload_response.json().get('file_url')
            logger.debug(f'Documento subido exitosamente. URL: {file_url}')

        except Exception as e:
            logger.error(f'Error durante la decodificación de base64: {str(e)}')
            return jsonify({
                "error": "Error en la decodificación base64",
                "details": str(e),
                "data_length": len(base64_data) if base64_data else 0
            }), 400

        finally:
            # Asegurar que el archivo temporal se elimine
            if 'temp_file_name' in locals():
                try:
                    os.remove(temp_file_name)
                    logger.debug('Archivo temporal eliminado')
                except Exception as e:
                    logger.warning(f'Error al eliminar archivo temporal: {str(e)}')

        return jsonify({
            "file_type": doc_type,
            "file_url": file_url,
            "file_name": data['source'].get('name', file_name),
            "file_size": file_size,
            "source": {
                "type": "base64",
                "media_type": data['source'].get('media_type', f'application/{doc_type}'),
                "data": text_result,  # Aquí se coloca el texto procesado
                "status": "success"
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error durante el procesamiento del documento: {str(e)}')
        return jsonify({
            "error": "Error en el procesamiento del documento",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    logger.info('Iniciando aplicación Flask')
    app.run(debug=True, host='0.0.0.0', port=7272)