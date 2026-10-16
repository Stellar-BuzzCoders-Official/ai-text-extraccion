import logging
import os
import tempfile
from src.ports.image_ports.doc_to_image_port import DocToImagePort
from src.adapters.image_adapters.docx_to_image_adapter import DocxToImageAdapter
import docx

# Configure the logger
logger = logging.getLogger(__name__)

class DocToImageAdapter(DocToImagePort):
    def __init__(self, doc_stream):
        self.doc_stream = doc_stream
        logger.info("DocToImageAdapter initialized with document stream")

    def convert_to_image(self):
        logger.debug("Starting document to image conversion")
        try:
            # Create a temporary DOCX file from the DOC stream
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_docx:
                logger.debug(f"Created temporary DOCX file: {temp_docx.name}")

                # Convert DOC to DOCX using python-docx
                if isinstance(self.doc_stream, str):
                    # If doc_stream is a file path, open the file
                    doc = docx.Document(self.doc_stream)
                else:
                    # If doc_stream is a file-like object, read the content and create a new document
                    doc = docx.Document()
                    doc.add_paragraph(self.doc_stream.read())
                doc.save(temp_docx.name)

            # Use the DocxToImageAdapter to convert DOCX to images
            docx_adapter = DocxToImageAdapter(temp_docx.name)
            images = docx_adapter.convert_to_image()

            logger.info(f"Conversion completed. {len(images)} images generated")
            os.remove(temp_docx.name)
            return images

        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            raise