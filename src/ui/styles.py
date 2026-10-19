"""
Vaani RAG — Custom Dark Theme CSS
Streamlit ki default UI ko override karke
ek professional dark theme deta hai.
"""


def get_main_css() -> str:
    """
    Main app ka CSS return karo.
    app.py mein st.markdown() se inject hoga.
    """
    return """
<style>
/* ============================================
   FONTS — Google Fonts import
   ============================================ */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ============================================
   ROOT VARIABLES — Dark Theme Colors
   ============================================ */
:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #111118;
    --bg-card: #1a1a24;
    --bg-hover: #22222e;

    --accent-primary: #7c3aed;
    --accent-secondary: #4f46e5;
    --accent-glow: rgba(124, 58, 237, 0.3);

    --text-primary: #f1f0f7;
    --text-secondary: #9d9ab5;
    --text-muted: #6b6883;

    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --info: #3b82f6;

    --border: rgba(124, 58, 237, 0.2);
    --border-hover: rgba(124, 58, 237, 0.5);

    --radius: 12px;
    --radius-lg: 20px;
    --shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    --shadow-glow: 0 0 40px rgba(124, 58, 237, 0.15);
}

/* ============================================
   BASE — App background aur font
   ============================================ */
.stApp {
    background-color: var(--bg-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Background texture — subtle grid pattern */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        linear-gradient(rgba(124, 58, 237, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(124, 58, 237, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ============================================
   SIDEBAR
   ============================================ */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .stMarkdown {
    color: var(--text-primary) !important;
}

/* ============================================
   HEADER — App title area
   ============================================ */
.vaani-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
    position: relative;
}

.vaani-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7c3aed, #4f46e5, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.5px;
}

.vaani-subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
    margin-top: 0.5rem;
    font-weight: 400;
}

/* ============================================
   CHAT MESSAGES
   ============================================ */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem 0;
}

/* User message — right side */
.user-message {
    display: flex;
    justify-content: flex-end;
    animation: slideInRight 0.3s ease;
}

.user-bubble {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: white;
    padding: 0.875rem 1.25rem;
    border-radius: var(--radius-lg) var(--radius-lg) 4px var(--radius-lg);
    max-width: 70%;
    font-size: 0.95rem;
    line-height: 1.6;
    box-shadow: var(--shadow), var(--shadow-glow);
}

/* Assistant message — left side */
.assistant-message {
    display: flex;
    justify-content: flex-start;
    animation: slideInLeft 0.3s ease;
}

.assistant-bubble {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 0.875rem 1.25rem;
    border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) 4px;
    max-width: 75%;
    font-size: 0.95rem;
    line-height: 1.7;
    box-shadow: var(--shadow);
}

.assistant-bubble:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow), var(--shadow-glow);
    transition: all 0.2s ease;
}

/* Message avatar icons */
.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    margin: 0 0.5rem;
}

.user-avatar {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
}

.assistant-avatar {
    background: var(--bg-hover);
    border: 1px solid var(--border);
}

/* ============================================
   CONFIDENCE BADGE
   ============================================ */
.confidence-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
}

.confidence-high {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.confidence-medium {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.confidence-low {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.confidence-info {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

/* ============================================
   DOCUMENT CARD — Sidebar mein
   ============================================ */
.doc-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    margin: 0.5rem 0;
    transition: all 0.2s ease;
}

.doc-card:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-glow);
    transform: translateY(-1px);
}

.doc-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 0.5rem 0;
}

.doc-stats {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
}

/* ============================================
   TREE VISUALIZATION — Sidebar mein
   ============================================ */
.tree-container {
    padding: 0.5rem 0;
}

.tree-node {
    padding: 0.5rem 0.75rem;
    margin: 0.25rem 0;
    border-left: 2px solid var(--accent-primary);
    background: var(--bg-card);
    border-radius: 0 var(--radius) var(--radius) 0;
    font-size: 0.8rem;
    color: var(--text-secondary);
    transition: all 0.2s ease;
}

.tree-node:hover {
    color: var(--text-primary);
    background: var(--bg-hover);
    border-left-color: var(--accent-secondary);
}

.tree-node-title {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.85rem;
}

.tree-child {
    margin-left: 1rem;
    border-left: 2px solid var(--accent-secondary);
    opacity: 0.8;
}

.tree-pages {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent-primary);
    margin-top: 0.2rem;
}

/* ============================================
   LANGUAGE SELECTOR
   ============================================ */
.lang-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
    background: rgba(124, 58, 237, 0.15);
    color: var(--accent-primary);
    border: 1px solid var(--border);
}

/* ============================================
   STATUS INDICATORS
   ============================================ */
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 0.4rem;
}

.status-ready { background: var(--success); }
.status-loading { background: var(--warning); animation: pulse 1s infinite; }
.status-error { background: var(--error); }

/* ============================================
   STREAMLIT OVERRIDES
   ============================================ */

/* Input box */
.stTextInput input, .stTextArea textarea {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* Selectbox */
.stSelectbox select, [data-testid="stSelectbox"] {
    background-color: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius-lg) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-primary) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* Divider */
hr {
    border-color: var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* Spinner */
.stSpinner {
    color: var(--accent-primary) !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}

/* ============================================
   ANIMATIONS
   ============================================ */
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(20px); }
    to   { opacity: 1; transform: translateX(0); }
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to   { opacity: 1; transform: translateX(0); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ============================================
   SCROLLBAR — Custom dark scrollbar
   ============================================ */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb {
    background: var(--accent-primary);
    border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover { background: var(--accent-secondary); }

/* ============================================
   MOBILE RESPONSIVE
   ============================================ */
@media (max-width: 768px) {
    .vaani-title { font-size: 2rem; }
    .user-bubble, .assistant-bubble { max-width: 90%; }
}
</style>
"""


def get_confidence_badge_html(score: float, label: str) -> str:
    """
    Confidence badge ka HTML return karo.
    Chat message ke neeche show hoga.
    """
    if "general knowledge" in label.lower():
        return f"""
<div class="confidence-badge confidence-info">
    🌐 {label}
</div>
"""

    if score >= 0.8:
        css_class = "confidence-high"
        icon = "✅"
    elif score >= 0.6:
        css_class = "confidence-medium"
        icon = "🟡"
    else:
        css_class = "confidence-low"
        icon = "⚠️"

    return f"""
<div class="confidence-badge {css_class}">
    {icon} Confidence: {label} ({score:.0%})
</div>
"""


def get_user_message_html(text: str) -> str:
    """User message bubble ka HTML return karo."""
    return f"""
<div class="user-message">
    <div class="user-bubble">{text}</div>
    <div class="message-avatar user-avatar">👤</div>
</div>
"""


def get_assistant_message_html(text: str, confidence_html: str = "") -> str:
    """Assistant message bubble ka HTML return karo."""
    return f"""
<div class="assistant-message">
    <div class="message-avatar assistant-avatar">🎙️</div>
    <div>
        <div class="assistant-bubble">{text}</div>
        {confidence_html}
    </div>
</div>
"""


def get_tree_node_html(title: str, pages: str, summary: str, is_child: bool = False) -> str:
    """
    Tree visualization node ka HTML return karo.
    Sidebar mein document structure show karne ke liye.
    """
    child_class = "tree-child" if is_child else ""
    return f"""
<div class="tree-node {child_class}">
    <div class="tree-node-title">📄 {title}</div>
    <div class="tree-pages">Pages {pages}</div>
    <div style="font-size: 0.75rem; color: #6b6883; margin-top: 0.3rem;">
        {summary[:80]}...
    </div>
</div>
"""


def get_doc_card_html(filename: str, pages: int, words: int, sections: int) -> str:
    """
    Document info card ka HTML return karo.
    Sidebar mein loaded document ki info show karne ke liye.
    """
    return f"""
<div class="doc-card">
    <div class="doc-title">📄 {filename}</div>
    <div class="doc-stats">
        📑 {pages} pages &nbsp;|&nbsp;
        📝 {words:,} words &nbsp;|&nbsp;
        🌳 {sections} sections
    </div>
</div>
"""


__all__ = [
    "get_main_css",
    "get_confidence_badge_html",
    "get_user_message_html",
    "get_assistant_message_html",
    "get_tree_node_html",
    "get_doc_card_html",
]
