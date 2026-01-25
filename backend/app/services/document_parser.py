"""
Document parser using unstructured library for PDF processing.
Extracts text, tables, and images with proper metadata.
"""
import os
from typing import List, Dict, Any
from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Element, Image, Table
import uuid


class DocumentParser:
    def __init__(self, output_dir: str = "outputs/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_pdf(self, pdf_path: str, document_id: str) -> Dict[str, Any]:
        """
        Parse PDF using unstructured with hi_res strategy.
        Returns structured document with text, tables, and images.
        """
        # Partition PDF with hi_res strategy for better accuracy
        elements = partition_pdf(
            filename=pdf_path,
            strategy="fast",
            extract_images_in_pdf=True,
            extract_image_block_types=["Image", "Table"],
            extract_image_block_to_payload=False,
        )

        # Process elements
        chunks = []
        image_paths = []
        chunk_index = 0

        for element in elements:
            metadata = element.metadata.to_dict() if hasattr(element.metadata, 'to_dict') else {}
            page_number = metadata.get('page_number', 1)

            if isinstance(element, Image):
                # Extract and save image
                image_path = self._extract_image(element, document_id, chunk_index)
                if image_path:
                    image_paths.append(image_path)
                    
                    # Create chunk for image with description
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_index}",
                        "document_id": document_id,
                        "content": element.text or f"Image on page {page_number}",
                        "content_type": "image",
                        "page_number": page_number,
                        "image_path": image_path,
                        "metadata": metadata
                    })
                    chunk_index += 1

            elif isinstance(element, Table):
                # Extract table as text only (no HTML)
                table_text = element.text or element.metadata.text_as_html or ""
                
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{chunk_index}",
                    "document_id": document_id,
                    "content": table_text,
                    "content_type": "table",
                    "page_number": page_number,
                    "metadata": metadata
                })
                chunk_index += 1

            else:
                # Regular text element
                text_content = element.text
                if text_content and len(text_content.strip()) > 0:
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_index}",
                        "document_id": document_id,
                        "content": text_content,
                        "content_type": "text",
                        "page_number": page_number,
                        "metadata": metadata
                    })
                    chunk_index += 1

        return {
            "document_id": document_id,
            "chunks": chunks,
            "image_paths": image_paths,
            "total_chunks": len(chunks)
        }

    def _extract_image(self, element: Image, document_id: str, index: int) -> str:
        """
        Extract and save image from element.
        Returns the saved image path.
        """
        try:
            # Generate unique filename
            image_filename = f"{document_id}_image_{index}_{uuid.uuid4().hex[:8]}.png"
            image_path = self.output_dir / image_filename

            # Get image data from element
            if hasattr(element, 'image'):
                # Save image
                with open(image_path, 'wb') as f:
                    f.write(element.image)
                return str(image_path)
            
            return None

        except Exception as e:
            print(f"Error extracting image: {e}")
            return None