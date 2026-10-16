import json
from src.ports.api_document_adapter.json_to_text_port import JsonPort   # noqa: F401

class JsonAdapter(JsonPort):
    def to_escaped_string(self, json_string: str) -> str:
        try:
            # Aquí convertimos el JSON ya decodificado a una cadena JSON escapada
            json_data = json.loads(json_string)
            return json.dumps(json_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error procesando JSON: {str(e)}")
