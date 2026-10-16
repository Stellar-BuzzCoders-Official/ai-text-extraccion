
```
qava-cn-ai-storage-text-extraction-backend
├─ .env
├─ .gitignore
├─ app.py
├─ docker-compose.yml
├─ Dockerfile
├─ install.sh
├─ README.md
├─ requirements.txt
├─ src
│  ├─ adapters
│  │  └─ image_adapters
│  │     ├─ docx_to_image_adapter.py
│  │     ├─ doc_to_image_adapter.py
│  │     ├─ image_to_text_adapter.py
│  │     ├─ pdf_to_image_adapter.py
│  │     ├─ pptx_to_image_adapter.py
│  │     └─ ppt_to_image_adapter.py
│  ├─ domain
│  ├─ ports
│  │  └─ image_ports
│  │     ├─ docx_to_image_port.py
│  │     ├─ doc_to_image_port.py
│  │     ├─ image_to_text_port.py
│  │     ├─ pdf_to_image_port.py
│  │     ├─ pptx_to_image_port.py
│  │     ├─ ppt_to_image_port.py
│  │     └─ __init__.py
│  └─ services
│     ├─ image_services
│     │  ├─ image_to_text_service.py
│     │  ├─ to_image_service.py
│     │  └─ __init__.py
│     └─ text_extraction_service.py
├─ start.sh
└─ stop.sh

```