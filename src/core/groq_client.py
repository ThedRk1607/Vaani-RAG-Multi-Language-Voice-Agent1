"""
Vaani RAG — Groq Client
Groq API ka wrapper hai ye file.

Kyun Groq?
- Sabse fast LLM inference available hai
- Voice agent ke liye speed critical hai
- Free tier available hai
- LLaMA3-70b model powerful + fast dono hai
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_groq import ChatGroq
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage
from src.utils.logger import logger

load_dotenv()


@dataclass
class GroqResponse:
    """
    Groq API ka structured response.
    Answer ke saath metadata bhi store hota hai.
    """
    answer: str
    model: str
    language: str
    confidence_score: float
    source_found: bool


class GroqClient:
    """
    Groq API ke saath interact karta hai.

    Ye file 2 kaam karti hai:
    1. LLM instance create karna (TreeBuilder ke liye)
    2. RAG query answer karna (user questions ke liye)
    """

    # Supported Groq models
    AVAILABLE_MODELS = {
        "openai/gpt-oss-120b": "GPT-OSS 120B (Best Quality)",
        "qwen/qwen3.8-27b": "Qwen 3.8 27B (Multilingual)",
        "openai/gpt-oss-20b": "GPT-OSS 20B (Fast)",
        "llama3-70b-8192": "LLaMA3 70B (Legacy)",
        "llama3-8b-8192": "LLaMA3 8B (Legacy)",
        "mixtral-8x7b-32768": "Mixtral 8x7B (Legacy)",
    }

    def __init__(self) -> None:
        """
        GroqClient initialize karo.
        API key environment variable se load hoti hai.
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.1"))

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found! "
                "Please add it to your .env file."
            )

        logger.info(f"GroqClient initialized with model: {self.model_name}")

    def get_llm(self) -> ChatGroq:
        """
        LangChain compatible LLM instance return karo.
        TreeBuilder aur RAGPipeline dono ye use karte hain.

        Returns:
            ChatGroq instance
        """
        return ChatGroq(
            api_key=self.api_key,
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

    def answer_from_tree(
        self,
        question: str,
        tree_context: str,
        document_summary: str,
        language_instruction: str,
    ) -> GroqResponse:
        """
        User ka question answer karo — document context se ya general knowledge se.

        Args:
            question: User ka question
            tree_context: Relevant tree nodes ka content
            document_summary: Document ka overall summary
            language_instruction: Kis language mein answer dena hai

        Returns:
            GroqResponse — answer + metadata
        """
        logger.info(f"Answering question: '{question[:50]}...'")

        # System prompt — Document first, general knowledge fallback
        system_prompt = f"""You are Vaani, an intelligent and helpful multilingual voice assistant.

CORE GUIDELINES:
1. Document Questions:
   - If the user's question relates to or can be answered using the uploaded document context or document overview, provide an accurate, fact-based answer prioritizing the document information.
   - If the user asks about the document itself (such as "What is my name?", "Summarize this document", "What projects are listed?"), use all provided document context and overview to give a direct, accurate answer.

2. Questions Outside the Document (General Knowledge & Conversation):
   - If the user asks a question that is NOT found in the document (such as general knowledge, history, coding concepts, science, or general conversation), answer it accurately, helpfully, and comprehensively using your general knowledge!
   - Do NOT refuse to answer. Provide the real answer clearly.

3. Source Tagging:
   - At the VERY END of your response, on a new line, add:
     [Source: Document] -> if the answer was derived from the uploaded document context/overview.
     [Source: General Knowledge] -> if the answer was derived from general knowledge outside the document.

4. Language:
   - {language_instruction}

5. Voice Optimization:
   - Keep answers clear, natural, and well-structured, suitable for voice speech playback.

Document Overview:
{document_summary if document_summary else "No document overview available."}
"""

        # User prompt — context + question
        user_prompt = f"""Document Context:
{tree_context if tree_context.strip() else "No specific section matches found."}

Question: {question}

Answer:"""

        try:
            llm = self.get_llm()

            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])

            raw_answer = response.content.strip()

            # Source tagging check
            source_found = True
            lower_raw = raw_answer.lower()
            if "[source: general knowledge]" in lower_raw:
                source_found = False
                clean_answer = (
                    raw_answer.replace("[Source: General Knowledge]", "")
                    .replace("[source: general knowledge]", "")
                    .strip()
                )
            elif "[source: document]" in lower_raw:
                source_found = True
                clean_answer = (
                    raw_answer.replace("[Source: Document]", "")
                    .replace("[source: document]", "")
                    .strip()
                )
            else:
                if "not available in the provided document" in lower_raw or not tree_context.strip():
                    source_found = False
                else:
                    source_found = True
                clean_answer = raw_answer

            # Confidence score calculate karo
            confidence = self._calculate_confidence(
                answer=clean_answer,
                context=tree_context + " " + document_summary,
                source_found=source_found,
            )

            logger.success(
                f"Answer generated — "
                f"confidence: {confidence:.2f}, "
                f"source_found: {source_found}"
            )

            return GroqResponse(
                answer=clean_answer,
                model=self.model_name,
                language=language_instruction,
                confidence_score=confidence,
                source_found=source_found,
            )

        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    def _calculate_confidence(
        self,
        answer: str,
        context: str,
        source_found: bool,
    ) -> float:
        """
        Answer ka confidence score calculate karo (0.0 to 1.0).
        """
        if not source_found:
            return 0.70  # Solid confidence for general knowledge answers

        if len(answer.split()) < 3:
            return 0.50

        # Context aur answer ke common words check karo
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())

        if not context_words:
            return 0.60

        overlap = len(answer_words.intersection(context_words))
        overlap_ratio = overlap / len(answer_words)

        if overlap_ratio > 0.35:
            score = 0.95
        elif overlap_ratio > 0.20:
            score = 0.85
        elif overlap_ratio > 0.05:
            score = 0.75
        else:
            score = 0.65

        return round(score, 2)

    def get_model_info(self) -> dict:
        """
        Current model ki info return karo.
        UI mein show hogi ye information.
        """
        return {
            "model": self.model_name,
            "display_name": self.AVAILABLE_MODELS.get(
                self.model_name,
                self.model_name
            ),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


__all__ = ["GroqClient", "GroqResponse"]
