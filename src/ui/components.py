"""
Vaani RAG — UI Components
Reusable Streamlit components hain ye sab.
Har component ek specific UI part render karta hai.
"""

import streamlit as st
from src.ui.styles import (
    get_confidence_badge_html,
    get_user_message_html,
    get_assistant_message_html,
    get_tree_node_html,
    get_doc_card_html,
)
from src.utils.language_detector import LANGUAGE_CONFIG
from src.utils.logger import logger


def render_header() -> None:
    """
    App ka main header render karo.
    Top pe show hoga — title + subtitle.
    """
    st.markdown("""
<div class="vaani-header">
    <h1 class="vaani-title">🎙️ Vaani RAG</h1>
    <p class="vaani-subtitle">
        Multilingual Voice Agent — Hindi • English • Bengali • Marathi • Bhojpuri
    </p>
</div>
""", unsafe_allow_html=True)


def render_sidebar_document_section() -> tuple[bytes | None, str | None]:
    """
    Sidebar mein document upload section render karo.

    Returns:
        tuple:
            - uploaded_bytes: User ne jo PDF upload ki uske bytes
            - selected_sample: Pre-loaded sample doc ka path
    """
    st.sidebar.markdown("## 📄 Documents")
    st.sidebar.markdown("---")

    uploaded_bytes = None
    selected_sample = None

    # Tab 1: Runtime upload
    # Tab 2: Pre-loaded samples
    upload_tab, sample_tab = st.sidebar.tabs(["📤 Upload", "📚 Samples"])

    with upload_tab:
        uploaded_file = st.file_uploader(
            label="Upload your PDF",
            type=["pdf"],
            help="PDF file upload karo jisse question poochna hai",
        )
        if uploaded_file:
            uploaded_bytes = uploaded_file.read()
            logger.info(f"File uploaded: {uploaded_file.name}")

    with sample_tab:
        # Sample documents list
        sample_docs = {
            "None": None,
            "📘 AI Basics": "assets/sample_docs/ai_basics.pdf",
            "📗 Machine Learning": "assets/sample_docs/ml_intro.pdf",
        }

        selected_label = st.selectbox(
            label="Select a sample document",
            options=list(sample_docs.keys()),
        )

        if selected_label != "None":
            selected_sample = sample_docs[selected_label]

    return uploaded_bytes, selected_sample


def render_sidebar_language_section() -> str:
    """
    Sidebar mein language selector render karo.

    Returns:
        str: Selected language code ('auto' ya specific language)
    """
    st.sidebar.markdown("## 🌍 Language")
    st.sidebar.markdown("---")

    language_options = {"🔄 Auto Detect": "auto"}

    for code, lang in LANGUAGE_CONFIG.items():
        language_options[f"🗣️ {lang.name}"] = code

    selected_label = st.sidebar.selectbox(
        label="Select Language",
        options=list(language_options.keys()),
        help="Auto Detect recommended hai — app khud language samjhega",
    )

    selected_code = language_options[selected_label]

    # Selected language badge show karo
    if selected_code != "auto":
        st.sidebar.markdown(
            f'<span class="lang-badge">🌍 {LANGUAGE_CONFIG[selected_code].name}</span>',
            unsafe_allow_html=True,
        )

    return selected_code


def render_sidebar_tree_section(tree_structure: list[dict]) -> None:
    """
    Sidebar mein JSON Tree visualization render karo.

    Args:
        tree_structure: RAGPipeline.get_tree_structure() ka output
    """
    if not tree_structure:
        return

    st.sidebar.markdown("## 🌳 Document Tree")
    st.sidebar.markdown("---")

    with st.sidebar.expander("View Tree Structure", expanded=False):
        for node in tree_structure:
            # Parent node
            st.markdown(
                get_tree_node_html(
                    title=node["title"],
                    pages=node["pages"],
                    summary=node["summary"],
                    is_child=False,
                ),
                unsafe_allow_html=True,
            )

            # Children nodes
            for child in node.get("children", []):
                st.markdown(
                    get_tree_node_html(
                        title=child["title"],
                        pages=child["pages"],
                        summary=child["summary"],
                        is_child=True,
                    ),
                    unsafe_allow_html=True,
                )


def render_sidebar_doc_info(stats: dict) -> None:
    """
    Sidebar mein loaded document ki info render karo.

    Args:
        stats: PDFParser.get_stats() ka output
    """
    st.sidebar.markdown("## 📊 Document Info")
    st.sidebar.markdown("---")

    st.sidebar.markdown(
        get_doc_card_html(
            filename=stats.get("filename", "Unknown"),
            pages=stats.get("total_pages", 0),
            words=stats.get("total_words", 0),
            sections=stats.get("tree_sections", 0),
        ),
        unsafe_allow_html=True,
    )

    # Document summary expander
    if stats.get("document_summary"):
        with st.sidebar.expander("📝 Document Summary"):
            st.write(stats["document_summary"])


def render_chat_message(
    role: str,
    content: str,
    confidence_score: float | None = None,
    confidence_label: str | None = None,
) -> None:
    """
    Ek chat message render karo.

    Args:
        role: 'user' ya 'assistant'
        content: Message text
        confidence_score: Answer ka confidence (sirf assistant ke liye)
        confidence_label: Human readable label (High/Medium/Low)
    """
    if role == "user":
        st.markdown(
            get_user_message_html(content),
            unsafe_allow_html=True,
        )
    else:
        # Confidence badge banao
        confidence_html = ""
        if confidence_score is not None and confidence_label:
            confidence_html = get_confidence_badge_html(
                score=confidence_score,
                label=confidence_label,
            )

        st.markdown(
            get_assistant_message_html(content, confidence_html),
            unsafe_allow_html=True,
        )


def render_chat_history(messages: list[dict]) -> None:
    """
    Poori chat history render karo.

    Args:
        messages: st.session_state.messages list
    """
    for message in messages:
        render_chat_message(
            role=message["role"],
            content=message["content"],
            confidence_score=message.get("confidence_score"),
            confidence_label=message.get("confidence_label"),
        )


def render_voice_input_section() -> bytes | None:
    """
    Voice input section render karo.
    Mic recorder + fallback audio upload dono.

    Returns:
        bytes | None: Audio bytes ya None
    """
    st.markdown("#### 🎤 Voice Input")

    col1, col2 = st.columns([1, 1])
    audio_bytes = None

    with col1:
        # Primary: Browser mic recorder
        try:
            from streamlit_mic_recorder import mic_recorder
            audio = mic_recorder(
                start_prompt="🎤 Start Recording",
                stop_prompt="⏹️ Stop Recording",
                just_once=True,
                key="mic_recorder",
            )
            if audio:
                audio_bytes = audio["bytes"]
                st.success("✅ Audio recorded!")
        except Exception as e:
            logger.warning(f"Mic recorder failed: {e}")
            st.info("Mic recorder unavailable — use file upload")

    with col2:
        # Fallback: Audio file upload
        audio_file = st.file_uploader(
            label="Or upload audio file",
            type=["wav", "mp3", "m4a", "ogg"],
            key="audio_uploader",
            help="Mic kaam na kare toh audio file upload karo",
        )
        if audio_file:
            audio_bytes = audio_file.read()
            st.success("✅ Audio file loaded!")

    return audio_bytes


def render_text_input_section() -> str | None:
    """
    Text input section render karo.

    Returns:
        str | None: User ka question ya None
    """
    question = st.chat_input(
        placeholder="Type your question here... (any language)",
    )
    return question


def render_pipeline_status(is_ready: bool, doc_name: str | None) -> None:
    """
    Pipeline status indicator render karo.
    Document loaded hai ya nahi show karta hai.
    """
    if is_ready and doc_name:
        st.markdown(
            f'<div style="text-align:center; padding: 0.5rem;">'
            f'<span class="status-dot status-ready"></span>'
            f'<span style="color: #10b981; font-size: 0.85rem;">'
            f'Ready — {doc_name}'
            f'</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="text-align:center; padding: 0.5rem;">'
            '<span class="status-dot status-error"></span>'
            '<span style="color: #ef4444; font-size: 0.85rem;">'
            'No document loaded — Please upload a PDF'
            '</span></div>',
            unsafe_allow_html=True,
        )


def render_audio_player(audio_bytes: bytes) -> None:
    """
    TTS audio player render karo.
    Answer sunne ke liye.

    Args:
        audio_bytes: gTTS ka output (MP3 bytes)
    """
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)


def render_relevant_sections(sections: list[str]) -> None:
    """
    Answer ke liye use hue relevant sections show karo.
    Transparency ke liye — user dekh sakta hai answer kahan se aaya.

    Args:
        sections: Section titles list
    """
    if not sections:
        return

    with st.expander("📍 Sources Used", expanded=False):
        for section in sections:
            st.markdown(
                f'<div class="tree-node">'
                f'<span class="tree-node-title">📄 {section}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_model_info(model_info: dict) -> None:
    """
    Sidebar mein current model info render karo.

    Args:
        model_info: GroqClient.get_model_info() ka output
    """
    st.sidebar.markdown("## ⚡ Model Info")
    st.sidebar.markdown("---")

    st.sidebar.markdown(
        f"""
<div class="doc-card">
    <div class="doc-title">🤖 {model_info.get('display_name', 'Unknown')}</div>
    <div class="doc-stats">
        🌡️ Temp: {model_info.get('temperature', 0.1)} &nbsp;|&nbsp;
        📊 Max tokens: {model_info.get('max_tokens', 1024)}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


__all__ = [
    "render_header",
    "render_sidebar_document_section",
    "render_sidebar_language_section",
    "render_sidebar_tree_section",
    "render_sidebar_doc_info",
    "render_chat_message",
    "render_chat_history",
    "render_voice_input_section",
    "render_text_input_section",
    "render_pipeline_status",
    "render_audio_player",
    "render_relevant_sections",
    "render_model_info",
]
