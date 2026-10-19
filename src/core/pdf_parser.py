"""
Vaani RAG — PDF Parser
Ye file PDF aur LLM ke beech ka BRIDGE hai.

Flow:
PDF File → PDFParser → Plain Text → LLM
"""

from dataclasses import dataclass, field
from pathlib import Path
import pymupdf
from src.utils.logger import logger


@dataclass
class ParsedDocument:
    """
    PDF parsing ka structured output.
    Har PDF parse hone ke baad ye object banta hai.
    """
    filename: str
    total_pages: int
    full_text: str
    pages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        """Total words in the document."""
        return len(self.full_text.split())

    @property
    def is_empty(self) -> bool:
        """Check karo ki document mein kuch text hai ya nahi."""
        return len(self.full_text.strip()) == 0

    def get_preview(self, chars: int = 200) -> str:
        """Document ka short preview return karo."""
        return self.full_text[:chars] + "..." if len(self.full_text) > chars else self.full_text


class PDFParser:
    """
    PDF Parser — PDF files se text extract karta hai.

    Ye BRIDGE hai PDF aur LLM ke beech:
    PDF File → PDFParser → Plain Text → LLM

    Supported inputs:
    - File path (str ya Path object)
    - Raw bytes (uploaded file from Streamlit)
    """

    def parse(self, source: str | Path | bytes) -> ParsedDocument:
        """
        PDF ko parse karo — path ya bytes dono accept karta hai.

        Args:
            source: File path (str/Path) ya raw bytes

        Returns:
            ParsedDocument — extracted text + metadata
        """
        try:
            if isinstance(source, bytes):
                logger.info("Parsing PDF from uploaded bytes...")
                return self._parse_bytes(source)

            logger.info(f"Parsing PDF from path: {source}")
            return self._parse_file(Path(source))

        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            raise

    def _parse_file(self, path: Path) -> ParsedDocument:
        """File path se PDF parse karo."""
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        doc = pymupdf.open(str(path))
        return self._extract(doc, filename=path.name)

    def _parse_bytes(self, data: bytes) -> ParsedDocument:
        """
        Bytes se PDF parse karo.
        Streamlit file uploader se aata hai ye.
        """
        doc = pymupdf.open(stream=data, filetype="pdf")
        return self._extract(doc, filename="uploaded_document.pdf")

    def _extract(
        self,
        doc: pymupdf.Document,
        filename: str,
    ) -> ParsedDocument:
        """
        Core extraction logic.
        Har page ka text extract karta hai.
        """
        pages = []
        full_text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Page se text extract karo
            text = page.get_text("text")

            # Agar page mein text nahi — scanned image ho sakta hai
            if not text.strip():
                logger.warning(
                    f"Page {page_num + 1} has no extractable text "
                    f"— might be a scanned image"
                )
                text = (
                    f"[Page {page_num + 1}: No text found "
                    f"— this page might be a scanned image]"
                )

            pages.append({
                "page_number": page_num + 1,
                "text": text.strip(),
                "char_count": len(text),
                "word_count": len(text.split()),
            })

            full_text_parts.append(text)

        # Saare pages ka text join karo
        full_text = "\n\n".join(full_text_parts)

        # Document metadata extract karo
        metadata = doc.metadata or {}

        total_pages = len(pages)
        doc.close()

        logger.success(
            f"Parsed '{filename}': "
            f"{total_pages} pages, "
            f"{len(full_text.split())} words"
        )

        return ParsedDocument(
            filename=filename,
            total_pages=total_pages,
            full_text=full_text,
            pages=pages,
            metadata=metadata,
        )

    def get_page_range(
        self,
        parsed_doc: ParsedDocument,
        start: int,
        end: int,
    ) -> str:
        """
        Specific page range ka text return karo.
        Tree builder use karta hai ye — specific section ka content lene ke liye.

        Args:
            parsed_doc: Already parsed document
            start: Start page number (1-based)
            end: End page number (1-based)

        Returns:
            str: Selected pages ka combined text
        """
        selected_pages = [
            page["text"]
            for page in parsed_doc.pages
            if start <= page["page_number"] <= end
        ]

        return "\n\n".join(selected_pages)

    def get_stats(self, parsed_doc: ParsedDocument) -> dict:
        """
        Document ki basic stats return karo.
        UI mein show hogi ye information.
        """
        return {
            "filename": parsed_doc.filename,
            "total_pages": parsed_doc.total_pages,
            "total_words": parsed_doc.word_count,
            "total_chars": len(parsed_doc.full_text),
            "avg_words_per_page": (
                parsed_doc.word_count // parsed_doc.total_pages
                if parsed_doc.total_pages > 0
                else 0
            ),
            "is_empty": parsed_doc.is_empty,
            "metadata": parsed_doc.metadata,
        }


__all__ = ["PDFParser", "ParsedDocument"]
