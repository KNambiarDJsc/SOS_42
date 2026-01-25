"""
Document parser using unstructured library for PDF processing.
Extracts text, tables, and images with proper metadata.
"""
from typing import Dict, Any
from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Image, Table
import uuid


class DocumentParser:
    def __init__(self, output_dir: str | Path = "outputs/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_pdf(self, pdf_path: str, document_id: str) -> Dict[str, Any]:
        """
        Parse PDF using unstructured with hi_res strategy.
        Returns unified chunks list.
        """
        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
            extract_images_in_pdf=True,
            languages=["eng"],
            chunking_strategy="by_title",
            max_characters=1200,
            new_after_n_chars=1000,
        )

        chunks = []
        image_paths = []
        chunk_index = 0

        for element in elements:
            metadata = (
                element.metadata.to_dict()
                if hasattr(element.metadata, "to_dict")
                else {}
            )

            page_number = metadata.get("page_number", 1)

            # ---------------- IMAGE ----------------
            if isinstance(element, Image):
                image_path = self._extract_image(
                    element, document_id, chunk_index
                )

                if image_path:
                    image_paths.append(image_path)
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_index}",
                        "document_id": document_id,
                        "content": element.text or f"Image on page {page_number}",
                        "content_type": "image",
                        "page_number": page_number,
                        "image_path": image_path,
                        "metadata": metadata,
                    })
                    chunk_index += 1

            # ---------------- TABLE ----------------
            elif isinstance(element, Table):
                table_text = element.text or ""
                if table_text.strip():
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_index}",
                        "document_id": document_id,
                        "content": table_text,
                        "content_type": "table",
                        "page_number": page_number,
                        "metadata": metadata,
                    })
                    chunk_index += 1

            # ---------------- TEXT ----------------
            else:
                text = element.text
                if text and text.strip():
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_index}",
                        "document_id": document_id,
                        "content": text,
                        "content_type": "text",
                        "page_number": page_number,
                        "metadata": metadata,
                    })
                    chunk_index += 1

        return {
            "document_id": document_id,
            "chunks": chunks,
            "image_paths": image_paths,
            "total_chunks": len(chunks),
        }

    def _extract_image(self, element: Image, document_id: str, index: int):
        try:
            if not hasattr(element, "image") or element.image is None:
                return None

            filename = f"{document_id}_img_{index}_{uuid.uuid4().hex[:6]}.png"
            path = self.output_dir / filename

            with open(path, "wb") as f:
                f.write(element.image)

            return str(path)

        except Exception as e:
            print("Image extraction failed:", e)
            return None
