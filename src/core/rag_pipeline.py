"""
Vaani RAG — RAG Pipeline
Ye file saari cheezein ek saath connect karti hai.

Flow:
User Question
    ↓
Language Detect
    ↓
Tree mein relevant nodes dhundho
    ↓
Groq LLM se answer lo
    ↓
Response return karo
"""

from dataclasses import dataclass, field
from src.core.pdf_parser import PDFParser, ParsedDocument
from src.core.tree_builder import TreeBuilder, DocumentTree, TreeNode
from src.core.groq_client import GroqClient, GroqResponse
from src.utils.language_detector import LanguageDetector, LanguageResult
from src.utils.logger import logger


@dataclass
class RAGResponse:
    """
    RAG pipeline ka complete response.
    UI ko ye object milta hai display ke liye.
    """
    answer: str
    confidence_score: float
    source_found: bool
    language: LanguageResult
    relevant_sections: list[str] = field(default_factory=list)
    document_name: str = ""
    model_used: str = ""

    @property
    def confidence_label(self) -> str:
        """
        Confidence score ko human readable label mein convert karo.
        UI mein show hoga ye.
        """
        if not self.source_found:
            return "General Knowledge 🌐"
        if self.confidence_score >= 0.8:
            return "High ✅"
        elif self.confidence_score >= 0.6:
            return "Medium 🟡"
        elif self.confidence_score >= 0.4:
            return "Low ⚠️"
        else:
            return "Very Low ❌"

    @property
    def confidence_color(self) -> str:
        """
        Confidence ke hisaab se color return karo.
        Streamlit UI mein use hoga.
        """
        if not self.source_found:
            return "blue"
        if self.confidence_score >= 0.8:
            return "green"
        elif self.confidence_score >= 0.6:
            return "orange"
        else:
            return "red"


class RAGPipeline:
    """
    Complete Vectorless RAG Pipeline.

    Ye class saari components ko ek saath jodti hai:
    PDFParser + TreeBuilder + GroqClient + LanguageDetector

    Ek baar initialize karo — baar baar query karo!
    """

    def __init__(self) -> None:
        """
        RAG Pipeline initialize karo.
        Saare components yahan setup hote hain.
        """
        self.groq_client = GroqClient()
        self.pdf_parser = PDFParser()
        self.language_detector = LanguageDetector()
        self.tree_builder = TreeBuilder(
            llm=self.groq_client.get_llm()
        )

        # Current active document ka tree
        self._current_tree: DocumentTree | None = None
        self._current_doc: ParsedDocument | None = None

        logger.info("RAG Pipeline initialized successfully!")

    def load_document(self, source: str | bytes) -> dict:
        """
        Document load karo aur tree banao.

        Args:
            source: PDF file path ya uploaded bytes

        Returns:
            dict — document stats UI ke liye
        """
        logger.info("Loading document into RAG pipeline...")

        # Step 1: PDF parse karo
        self._current_doc = self.pdf_parser.parse(source)

        if self._current_doc.is_empty:
            raise ValueError(
                "Document appears to be empty or contains no extractable text. "
                "It might be a scanned PDF."
            )

        # Step 2: Tree banao (ya cache se load karo)
        self._current_tree = self.tree_builder.build(self._current_doc)

        stats = self.pdf_parser.get_stats(self._current_doc)
        stats["tree_sections"] = self._current_tree.total_sections
        stats["document_summary"] = self._current_tree.document_summary

        logger.success(
            f"Document loaded: '{self._current_doc.filename}' "
            f"with {self._current_tree.total_sections} sections"
        )

        return stats

    INTENT_SYNONYMS: dict[str, list[str]] = {
        "name": ["contact", "profile", "personal", "about", "candidate", "author", "header", "naam"],
        "who": ["contact", "profile", "personal", "about", "candidate", "author", "kaun"],
        "author": ["contact", "profile", "personal", "about", "author", "candidate"],
        "contact": ["contact", "email", "phone", "profile", "address", "social", "sampark"],
        "email": ["contact", "email", "profile", "mail"],
        "phone": ["contact", "phone", "mobile", "number"],
        "education": ["education", "degree", "academic", "university", "college", "school", "padhai", "shiksha"],
        "study": ["education", "degree", "academic", "university", "college", "school"],
        "college": ["education", "academic", "university", "college"],
        "school": ["education", "academic", "school"],
        "project": ["project", "projects", "work", "built", "portfolio"],
        "projects": ["project", "projects", "work", "built", "portfolio"],
        "experience": ["experience", "employment", "work", "job", "career"],
        "work": ["experience", "employment", "work", "project", "projects", "job"],
        "job": ["experience", "employment", "work", "career"],
        "skill": ["skill", "skills", "technical", "technologies", "tools", "stack"],
        "skills": ["skill", "skills", "technical", "technologies", "tools", "stack"],
        "summary": ["summary", "overview", "introduction", "abstract", "about"],
    }

    def query(
        self,
        question: str,
        language_override: str = "auto",
    ) -> RAGResponse:
        """
        User ke question ka answer generate karo.
        Document context se ya general knowledge se.

        Args:
            question: User ka question (text ya voice se)
            language_override: Manual language select ya 'auto'

        Returns:
            RAGResponse — complete response with metadata
        """
        if not self._current_tree or not self._current_doc:
            # Handle gracefully even if called without document
            detected_language = self.language_detector.detect(
                text=question,
                override=language_override,
            )
            groq_response = self.groq_client.answer_from_tree(
                question=question,
                tree_context="",
                document_summary="No document loaded.",
                language_instruction=detected_language.prompt_instruction,
            )
            return RAGResponse(
                answer=groq_response.answer,
                confidence_score=groq_response.confidence_score,
                source_found=False,
                language=detected_language,
                relevant_sections=[],
                document_name="",
                model_used=groq_response.model,
            )

        logger.info(f"Processing query: '{question[:60]}...'")

        # Step 1: Language detect karo
        detected_language = self.language_detector.detect(
            text=question,
            override=language_override,
        )
        logger.info(f"Language detected: {detected_language.name}")

        # Step 2: Relevant tree nodes dhundho
        relevant_nodes = self._retrieve_relevant_nodes(question)
        all_flat_nodes = self._current_tree.get_all_nodes_flat()

        # Fallback for small documents or when no specific section scored:
        if not relevant_nodes:
            if len(all_flat_nodes) <= 6:
                # Small document (like resume) — give full context to LLM
                relevant_nodes = all_flat_nodes
                logger.info(f"Using all {len(relevant_nodes)} nodes for complete document context")
            elif all_flat_nodes:
                # Large document — provide top sections as baseline context
                relevant_nodes = all_flat_nodes[:3]
                logger.info(f"Fallback to first {len(relevant_nodes)} nodes for context")

        # Step 3: Node content combine karo
        tree_context = self._build_context(relevant_nodes) if relevant_nodes else ""
        relevant_section_titles = [node.title for node in relevant_nodes] if relevant_nodes else []

        # Step 4: Groq se answer lo
        groq_response = self.groq_client.answer_from_tree(
            question=question,
            tree_context=tree_context,
            document_summary=self._current_tree.document_summary,
            language_instruction=detected_language.prompt_instruction,
        )

        return RAGResponse(
            answer=groq_response.answer,
            confidence_score=groq_response.confidence_score,
            source_found=groq_response.source_found,
            language=detected_language,
            relevant_sections=relevant_section_titles if groq_response.source_found else [],
            document_name=self._current_doc.filename,
            model_used=groq_response.model,
        )

    def _retrieve_relevant_nodes(
        self,
        question: str,
        top_k: int = 3,
    ) -> list[TreeNode]:
        """
        Question ke liye relevant tree nodes dhundho.
        """
        question_words = set(question.lower().split())

        # Stop words hata do
        stop_words = {
            "what", "is", "are", "the", "a", "an", "in", "of",
            "to", "and", "or", "how", "why", "when", "where",
            "tell", "me", "give", "kya", "hai", "kaise", "kyun",
            "kab", "kahan", "batao", "mujhe",
        }
        filtered_words = question_words - stop_words
        if not filtered_words:
            filtered_words = question_words

        # Expand with intent synonyms
        expanded_words = set(filtered_words)
        for w in filtered_words:
            if w in self.INTENT_SYNONYMS:
                expanded_words.update(self.INTENT_SYNONYMS[w])

        scored_nodes = []
        for node in self._current_tree.get_all_nodes_flat():
            score = self._score_node(node, expanded_words, question)
            if score > 0:
                scored_nodes.append((score, node))

        # Sort by score
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [node for _, node in scored_nodes[:top_k]]

        logger.info(
            f"Retrieved {len(top_nodes)} relevant nodes "
            f"from {len(self._current_tree.get_all_nodes_flat())} total"
        )
        return top_nodes

    def _score_node(
        self,
        node: TreeNode,
        expanded_words: set,
        full_question: str,
    ) -> float:
        """
        Ek node ko question ke relevance ke hisaab se score karo.
        """
        score = 0.0

        # Title match — high weight
        title_lower = node.title.lower()
        title_words = set(title_lower.split())
        title_matches = len(expanded_words.intersection(title_words))
        score += title_matches * 4.0

        # Summary match — medium weight
        summary_lower = node.summary.lower()
        summary_words = set(summary_lower.split())
        summary_matches = len(expanded_words.intersection(summary_words))
        score += summary_matches * 2.5

        # Content match
        content_lower = node.content.lower()
        for w in expanded_words:
            if len(w) > 2 and w in content_lower:
                score += 1.0

        # Exact phrase match bonus
        if full_question.strip().lower() in content_lower:
            score += 10.0

        return score

    def _build_context(self, nodes: list[TreeNode]) -> str:
        """
        Relevant nodes ka context string banao.
        Ye Groq LLM ko diya jaata hai.
        """
        context_parts = []

        for i, node in enumerate(nodes, 1):
            context_parts.append(
                f"[Section {i}: {node.title}]\n"
                f"Pages {node.page_start}-{node.page_end}\n"
                f"Summary: {node.summary}\n"
                f"Content: {node.content}\n"
            )

        return "\n---\n".join(context_parts)

    def _no_answer_response(
        self,
        language: LanguageResult,
    ) -> RAGResponse:
        """
        Jab koi relevant node na mile toh ye response return karo.
        """
        return RAGResponse(
            answer="This information is not available in the provided document.",
            confidence_score=0.0,
            source_found=False,
            language=language,
            relevant_sections=[],
            document_name=self._current_doc.filename if self._current_doc else "",
            model_used=self.groq_client.model_name,
        )

    @property
    def is_ready(self) -> bool:
        """Check karo ki pipeline use ke liye ready hai ya nahi."""
        return self._current_tree is not None

    @property
    def current_document_name(self) -> str | None:
        """Currently loaded document ka naam return karo."""
        return self._current_doc.filename if self._current_doc else None

    def get_tree_structure(self) -> list[dict]:
        """
        Tree structure return karo — UI visualization ke liye.
        Sidebar mein show hoga ye.
        """
        if not self._current_tree:
            return []

        structure = []
        for node in self._current_tree.nodes:
            structure.append({
                "title": node.title,
                "pages": f"{node.page_start}–{node.page_end}",
                "summary": node.summary,
                "children": [
                    {
                        "title": child.title,
                        "pages": f"{child.page_start}–{child.page_end}",
                        "summary": child.summary,
                    }
                    for child in node.children
                ],
            })

        return structure


__all__ = ["RAGPipeline", "RAGResponse"]
