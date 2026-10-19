"""
Vaani RAG — Tree Builder
Ye Vectorless RAG ka HEART hai!

Traditional RAG:
PDF → Chunks → Embeddings → Vector DB → Similarity Search

Vaani RAG (Vectorless):
PDF → LLM Tree Builder → JSON Index → LLM Traversal → Answer

Koi Vector DB nahi! Koi Embeddings nahi! Sirf ek JSON file! ✅
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict

from langchain_groq import ChatGroq
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage

from src.core.pdf_parser import ParsedDocument, PDFParser
from src.utils.logger import logger


@dataclass
class TreeNode:
    """
    Document tree ka ek node.
    Ek section ya subsection represent karta hai.
    """
    title: str
    summary: str
    page_start: int
    page_end: int
    content: str = ""
    children: list["TreeNode"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Node ko dictionary mein convert karo — JSON save ke liye."""
        return {
            "title": self.title,
            "summary": self.summary,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "content": self.content,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class DocumentTree:
    """
    Poore document ka tree index.
    Ye JSON file mein save hota hai — Vector DB ki jagah!
    """
    filename: str
    total_pages: int
    document_summary: str
    nodes: list[TreeNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Tree ko dictionary mein convert karo."""
        return {
            "filename": self.filename,
            "total_pages": self.total_pages,
            "document_summary": self.document_summary,
            "nodes": [node.to_dict() for node in self.nodes],
        }

    def to_json(self) -> str:
        """Tree ko JSON string mein convert karo."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @property
    def total_sections(self) -> int:
        """Total sections count karo."""
        return len(self.nodes)

    def get_all_nodes_flat(self) -> list[TreeNode]:
        """
        Saare nodes flat list mein return karo.
        Children bhi include honge.
        Search ke liye useful hai.
        """
        flat_list = []
        for node in self.nodes:
            flat_list.append(node)
            flat_list.extend(node.children)
        return flat_list


class TreeBuilder:
    """
    Parsed document se JSON Tree Index banata hai.

    Ye Vector DB ko REPLACE karta hai!

    Flow:
    ParsedDocument → LLM → Structure Analyze → JSON Tree → Cache mein save
    """

    CACHE_DIR = Path(".cache/trees")

    def __init__(self, llm: ChatGroq) -> None:
        """
        TreeBuilder initialize karo.

        Args:
            llm: Groq LLM instance — structure analyze karne ke liye
        """
        self.llm = llm
        self.parser = PDFParser()
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("TreeBuilder initialized")

    def build(self, parsed_doc: ParsedDocument) -> DocumentTree:
        """
        Document ka tree banao.
        Pehle cache check karta hai — agar already ban chuka hai toh rebuild nahi karta!

        Args:
            parsed_doc: PDFParser ka output

        Returns:
            DocumentTree — complete JSON tree index
        """
        # Cache check karo
        cache_key = self._get_cache_key(parsed_doc)
        cached_tree = self._load_from_cache(cache_key)

        if cached_tree:
            logger.info(f"Tree loaded from cache: {parsed_doc.filename}")
            return cached_tree

        # Naya tree banao
        logger.info(f"Building new tree for: {parsed_doc.filename}")
        tree = self._build_tree(parsed_doc)

        # Cache mein save karo
        self._save_to_cache(cache_key, tree)

        return tree

    def _build_tree(self, parsed_doc: ParsedDocument) -> DocumentTree:
        """
        Core tree building logic.
        LLM document ko analyze karta hai aur structure detect karta hai.
        """

        # Step 1: LLM se document structure analyze karwao
        logger.info("Asking LLM to analyze document structure...")

        structure_prompt = f"""You are analyzing a document to build a hierarchical tree index for a RAG system.

Document Name: {parsed_doc.filename}
Total Pages: {parsed_doc.total_pages}

Document Content (first 4000 characters):
{parsed_doc.full_text[:4000]}

Your task: Analyze this document and return a JSON structure.

Return ONLY this JSON format, nothing else:
{{
  "document_summary": "2-3 sentence overview of the entire document",
  "sections": [
    {{
      "title": "Section title",
      "page_start": 1,
      "page_end": 5,
      "summary": "What this section covers in 2-3 sentences",
      "subsections": [
        {{
          "title": "Subsection title",
          "page_start": 1,
          "page_end": 3,
          "summary": "What this subsection covers"
        }}
      ]
    }}
  ]
}}

Rules:
- Return ONLY valid JSON
- No markdown, no explanation
- Subsections list can be empty []
- Page numbers must be within 1 to {parsed_doc.total_pages}
"""

        try:
            response = self.llm.invoke([
                SystemMessage(
                    content="You are a document structure analyzer. Return only valid JSON, nothing else."
                ),
                HumanMessage(content=structure_prompt),
            ])

            # Response clean karo — markdown backticks remove karo
            raw = response.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()

            structure = json.loads(raw)
            logger.success("Document structure analyzed successfully!")

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"LLM structure analysis failed: {e}")
            logger.info("Using fallback structure...")
            structure = self._fallback_structure(parsed_doc)

        # Step 2: TreeNode objects banao
        nodes = []

        for section in structure.get("sections", []):
            page_start = max(1, section.get("page_start", 1))
            page_end = min(
                parsed_doc.total_pages,
                section.get("page_end", parsed_doc.total_pages)
            )

            # Section ka actual content lo
            section_content = self.parser.get_page_range(
                parsed_doc, page_start, page_end
            )

            # Children (subsections) banao
            children = []
            for sub in section.get("subsections", []):
                sub_start = max(1, sub.get("page_start", page_start))
                sub_end = min(parsed_doc.total_pages, sub.get("page_end", page_end))

                sub_content = self.parser.get_page_range(
                    parsed_doc, sub_start, sub_end
                )

                children.append(TreeNode(
                    title=sub.get("title", "Untitled Subsection"),
                    summary=sub.get("summary", ""),
                    page_start=sub_start,
                    page_end=sub_end,
                    content=sub_content[:1500],
                ))

            nodes.append(TreeNode(
                title=section.get("title", "Untitled Section"),
                summary=section.get("summary", ""),
                page_start=page_start,
                page_end=page_end,
                content=section_content[:2000],
                children=children,
            ))

        # Final DocumentTree banao
        tree = DocumentTree(
            filename=parsed_doc.filename,
            total_pages=parsed_doc.total_pages,
            document_summary=structure.get(
                "document_summary",
                "Document summary not available."
            ),
            nodes=nodes,
        )

        logger.success(
            f"Tree built: {len(nodes)} sections for '{parsed_doc.filename}'"
        )

        return tree

    def _fallback_structure(self, parsed_doc: ParsedDocument) -> dict:
        """
        Jab LLM fail ho jaaye toh simple fallback structure use karo.
        Document ko equal parts mein tod deta hai.
        """
        pages_per_section = max(1, parsed_doc.total_pages // 5)
        sections = []

        for i in range(0, parsed_doc.total_pages, pages_per_section):
            start = i + 1
            end = min(i + pages_per_section, parsed_doc.total_pages)
            sections.append({
                "title": f"Section {len(sections) + 1} (Pages {start}–{end})",
                "page_start": start,
                "page_end": end,
                "summary": f"Content from pages {start} to {end}.",
                "subsections": [],
            })

        return {
            "document_summary": f"Document with {parsed_doc.total_pages} pages.",
            "sections": sections,
        }

    def _get_cache_key(self, parsed_doc: ParsedDocument) -> str:
        """
        Document ka unique cache key banao.
        Filename + word count se hash banta hai.
        Same document dobara upload karo — same key milegi!
        """
        unique_string = f"{parsed_doc.filename}_{parsed_doc.word_count}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _save_to_cache(self, cache_key: str, tree: DocumentTree) -> None:
        """Tree ko JSON file mein save karo."""
        cache_path = self.CACHE_DIR / f"{cache_key}.json"

        try:
            cache_path.write_text(
                tree.to_json(),
                encoding="utf-8"
            )
            logger.info(f"Tree cached: {cache_path}")
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    def _load_from_cache(self, cache_key: str) -> DocumentTree | None:
        """
        Cache se tree load karo.
        Nahi mila toh None return karo.
        """
        cache_path = self.CACHE_DIR / f"{cache_key}.json"

        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            nodes = []

            for node_data in data.get("nodes", []):
                children = [
                    TreeNode(
                        title=child["title"],
                        summary=child["summary"],
                        page_start=child["page_start"],
                        page_end=child["page_end"],
                        content=child.get("content", ""),
                    )
                    for child in node_data.get("children", [])
                ]

                nodes.append(TreeNode(
                    title=node_data["title"],
                    summary=node_data["summary"],
                    page_start=node_data["page_start"],
                    page_end=node_data["page_end"],
                    content=node_data.get("content", ""),
                    children=children,
                ))

            return DocumentTree(
                filename=data["filename"],
                total_pages=data["total_pages"],
                document_summary=data["document_summary"],
                nodes=nodes,
            )

        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
            return None


__all__ = ["TreeBuilder", "DocumentTree", "TreeNode"]
