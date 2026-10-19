"""
Vaani RAG — Main Application Entry Point
Ye file sab kuch ek saath jodti hai aur Streamlit app run karti hai.

Run karne ke liye:
    streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv

# Environment variables load karo — sabse pehle!
load_dotenv()

from src.core.rag_pipeline import RAGPipeline
from src.utils.voice_handler import VoiceHandler
from src.ui.styles import get_main_css
from src.ui.components import (
    render_header,
    render_sidebar_document_section,
    render_sidebar_language_section,
    render_sidebar_tree_section,
    render_sidebar_doc_info,
    render_chat_message,
    render_chat_history,
    render_voice_input_section,
    render_text_input_section,
    render_pipeline_status,
    render_audio_player,
    render_relevant_sections,
    render_model_info,
)
from src.utils.logger import logger


# ============================================================
# PAGE CONFIG — Streamlit page settings
# ============================================================
st.set_page_config(
    page_title="Vaani RAG",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE — App ka memory
# Streamlit har rerun pe state reset karta hai
# isliye session_state use karte hain
# ============================================================
def initialize_session_state() -> None:
    """Session state initialize karo — sirf pehli baar."""

    if "messages" not in st.session_state:
        # Chat history store hoti hai yahan
        st.session_state.messages = []

    if "pipeline" not in st.session_state:
        # RAG Pipeline — ek baar banao, baar baar use karo
        st.session_state.pipeline = None

    if "voice_handler" not in st.session_state:
        # Voice Handler — STT + TTS
        st.session_state.voice_handler = None

    if "doc_stats" not in st.session_state:
        # Loaded document ki stats
        st.session_state.doc_stats = None

    if "pipeline_ready" not in st.session_state:
        st.session_state.pipeline_ready = False


def get_pipeline() -> RAGPipeline:
    """
    RAG Pipeline return karo.
    Agar nahi bani toh banao — Singleton pattern.
    """
    if st.session_state.pipeline is None:
        with st.spinner("⚡ Initializing Vaani RAG..."):
            st.session_state.pipeline = RAGPipeline()
        logger.info("RAG Pipeline created")
    return st.session_state.pipeline


def get_voice_handler() -> VoiceHandler:
    """
    Voice Handler return karo.
    Agar nahi bana toh banao — Singleton pattern.
    """
    if st.session_state.voice_handler is None:
        st.session_state.voice_handler = VoiceHandler(model_size="base")
        logger.info("Voice Handler created")
    return st.session_state.voice_handler


# ============================================================
# DOCUMENT LOADING
# ============================================================
def handle_document_loading(
    uploaded_bytes: bytes | None,
    selected_sample: str | None,
    pipeline: RAGPipeline,
) -> None:
    """
    Document load karo pipeline mein.

    Args:
        uploaded_bytes: User uploaded PDF bytes
        selected_sample: Sample doc path
        pipeline: RAG Pipeline instance
    """
    source = None

    if uploaded_bytes:
        source = uploaded_bytes
    elif selected_sample:
        source = selected_sample

    if source is None:
        return

    # Already same document loaded hai?
    if (
        st.session_state.pipeline_ready
        and st.session_state.doc_stats
        and source == uploaded_bytes
    ):
        return

    # Document load karo
    with st.spinner("📄 Loading document and building tree..."):
        try:
            stats = pipeline.load_document(source)
            st.session_state.doc_stats = stats
            st.session_state.pipeline_ready = True

            # Chat history clear karo — naya document, naya session
            st.session_state.messages = []

            st.success(
                f"✅ Document loaded: {stats['filename']} "
                f"({stats['total_pages']} pages, "
                f"{stats['tree_sections']} sections)"
            )
            logger.success(f"Document loaded successfully: {stats['filename']}")

        except Exception as e:
            st.error(f"❌ Failed to load document: {str(e)}")
            logger.error(f"Document loading failed: {e}")
            st.session_state.pipeline_ready = False


# ============================================================
# QUERY PROCESSING
# ============================================================
def process_query(
    question: str,
    pipeline: RAGPipeline,
    voice_handler: VoiceHandler,
    language_code: str,
    tts_enabled: bool,
) -> None:
    """
    User ka question process karo aur answer display karo.

    Args:
        question: User ka question (text)
        pipeline: RAG Pipeline instance
        voice_handler: Voice Handler instance
        language_code: Selected language
        tts_enabled: TTS on hai ya off
    """
    if not question.strip():
        return

    if not st.session_state.pipeline_ready:
        st.warning("⚠️ Please upload a document first!")
        return

    # User message chat history mein add karo
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    # User message render karo
    render_chat_message(role="user", content=question)

    # RAG pipeline se answer lo
    with st.spinner("🤔 Thinking..."):
        try:
            response = pipeline.query(
                question=question,
                language_override=language_code,
            )

            # Assistant message chat history mein add karo
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.answer,
                "confidence_score": response.confidence_score,
                "confidence_label": response.confidence_label,
            })

            # Answer render karo
            render_chat_message(
                role="assistant",
                content=response.answer,
                confidence_score=response.confidence_score,
                confidence_label=response.confidence_label,
            )

            # Sources show karo
            render_relevant_sections(response.relevant_sections)

            # TTS — answer sunao
            if tts_enabled and response.source_found:
                with st.spinner("🔊 Generating audio..."):
                    try:
                        audio_bytes = voice_handler.text_to_speech(
                            text=response.answer,
                            language_code=response.language.tts_code,
                        )
                        render_audio_player(audio_bytes)
                    except Exception as e:
                        logger.warning(f"TTS failed: {e}")
                        st.warning("⚠️ Audio generation failed")

            logger.info(
                f"Query processed — "
                f"confidence: {response.confidence_score}, "
                f"language: {response.language.name}"
            )

        except Exception as e:
            error_msg = f"Sorry, something went wrong: {str(e)}"
            st.error(f"❌ {error_msg}")
            logger.error(f"Query processing failed: {e}")


# ============================================================
# VOICE QUERY PROCESSING
# ============================================================
def process_voice_query(
    audio_bytes: bytes,
    pipeline: RAGPipeline,
    voice_handler: VoiceHandler,
    language_code: str,
) -> None:
    """
    Voice input process karo — STT karo phir query karo.

    Args:
        audio_bytes: Recorded audio bytes
        pipeline: RAG Pipeline instance
        voice_handler: Voice Handler instance
        language_code: Selected language
    """
    with st.spinner("🎤 Transcribing audio..."):
        try:
            transcription = voice_handler.transcribe(
                audio_bytes=audio_bytes,
                language_code=language_code,
            )

            if not transcription.text.strip():
                st.warning("⚠️ Could not transcribe audio — please try again")
                return

            st.info(f"🎤 Transcribed: *{transcription.text}*")

            # Transcribed text ko process karo
            process_query(
                question=transcription.text,
                pipeline=pipeline,
                voice_handler=voice_handler,
                language_code=language_code,
                tts_enabled=True,
            )

        except Exception as e:
            st.error(f"❌ Transcription failed: {str(e)}")
            logger.error(f"Voice transcription failed: {e}")


# ============================================================
# MAIN APP
# ============================================================
def main() -> None:
    """Main app function — sab kuch yahan se start hota hai."""

    # Session state initialize karo
    initialize_session_state()

    # CSS inject karo
    st.markdown(get_main_css(), unsafe_allow_html=True)

    # Components initialize karo
    pipeline = get_pipeline()
    voice_handler = get_voice_handler()

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------
    with st.sidebar:
        # Document upload section
        uploaded_bytes, selected_sample = render_sidebar_document_section()

        # Document load karo
        handle_document_loading(uploaded_bytes, selected_sample, pipeline)

        # Language selector
        language_code = render_sidebar_language_section()

        # TTS toggle
        st.sidebar.markdown("## 🔊 Voice Output")
        st.sidebar.markdown("---")
        tts_enabled = st.sidebar.toggle(
            label="Enable Text-to-Speech",
            value=True,
            help="Answer ko audio mein sunna chahte ho?",
        )

        # Document info show karo
        if st.session_state.doc_stats:
            render_sidebar_doc_info(st.session_state.doc_stats)

        # Tree visualization
        if st.session_state.pipeline_ready:
            tree_structure = pipeline.get_tree_structure()
            render_sidebar_tree_section(tree_structure)

        # Model info
        render_model_info(pipeline.groq_client.get_model_info())

        # Clear chat button
        st.sidebar.markdown("---")
        if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # --------------------------------------------------------
    # MAIN CONTENT
    # --------------------------------------------------------

    # Header
    render_header()

    # Pipeline status
    render_pipeline_status(
        is_ready=st.session_state.pipeline_ready,
        doc_name=pipeline.current_document_name,
    )

    st.markdown("---")

    # Document upload nahi hua toh welcome message
    if not st.session_state.pipeline_ready:
        st.markdown("""
<div style="text-align: center; padding: 3rem; color: #6b6883;">
    <div style="font-size: 4rem; margin-bottom: 1rem;">📄</div>
    <h3 style="color: #9d9ab5;">Upload a PDF to get started</h3>
    <p>Upload any PDF document from the sidebar<br>
    and start asking questions in any language!</p>
    <br>
    <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
        <span>🎤 Voice Input</span>
        <span>🔊 Voice Output</span>
        <span>🌍 6 Languages</span>
        <span>🌳 Smart Tree RAG</span>
    </div>
</div>
""", unsafe_allow_html=True)
        return

    # Chat history render karo
    render_chat_history(st.session_state.messages)

    # --------------------------------------------------------
    # INPUT SECTION — Voice + Text
    # --------------------------------------------------------
    st.markdown("---")

    input_tab1, input_tab2 = st.tabs(["💬 Text Input", "🎤 Voice Input"])

    with input_tab1:
        # Text input
        question = render_text_input_section()
        if question:
            process_query(
                question=question,
                pipeline=pipeline,
                voice_handler=voice_handler,
                language_code=language_code,
                tts_enabled=tts_enabled,
            )

    with input_tab2:
        # Voice input
        audio_bytes = render_voice_input_section()
        if audio_bytes:
            process_voice_query(
                audio_bytes=audio_bytes,
                pipeline=pipeline,
                voice_handler=voice_handler,
                language_code=language_code,
            )


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    main()
