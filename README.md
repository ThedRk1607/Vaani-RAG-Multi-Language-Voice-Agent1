# 🎙️ They are RAG — Multi-Language Voice Agent

<div align="center">

**A production-grade, vectorless RAG-powered voice agent supporting Hindi, English, Hinglish, Bengali, Marathi & Bhojpuri.**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#-configuration) • [Contributing](#-contributing) • [License](#-license)

</div>

---

## 📌 Overview

**Vaani RAG** is a multilingual voice-enabled Retrieval-Augmented Generation (RAG) system built for Indian languages. Unlike traditional RAG systems that rely on vector databases, Vaani RAG uses a **Vectorless RAG** approach powered by an LLM Tree Index — making it simpler to set up, cheaper to run, and more context-aware.

Ask questions about your PDF documents using your **voice** in any of 6 supported languages, and get accurate, sourced answers in the same language — spoken back to you.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎤 **Voice Input** | Speak your question using your microphone |
| 🔊 **Voice Output** | Hear the answer via Text-to-Speech |
| 🌍 **6 Languages** | Hindi, English, Hinglish, Bengali, Marathi, Bhojpuri |
| 📄 **PDF Upload** | Upload any PDF at runtime or use pre-loaded docs |
| 🌳 **Vectorless RAG** | JSON Tree Index — no Vector DB required |
| ⚡ **Groq Powered** | Ultra-fast LLM inference (sub-second responses) |
| 📊 **Confidence Score** | Know how reliable each answer is |
| 🌳 **Tree Visualization** | See the document structure in the sidebar |
| ⚡ **Cache System** | Rebuilt trees are cached — no reprocessing |
| 🎨 **Dark UI** | Clean, modern dark-themed Streamlit interface |

---

## 🏗️ Architecture

### Why Vectorless RAG?

Traditional RAG requires a heavy pipeline:
```
Document → Chunking → Embedding Model → Vector DB → Similarity Search → LLM → Answer
```

Vaani RAG simplifies this to:
```
Document → LLM Tree Builder → JSON Index → LLM Traversal → Answer
```

**Benefits:**
- ✅ No Vector DB setup or maintenance
- ✅ No embedding model or costs
- ✅ Better context preservation (no arbitrary chunking)
- ✅ Human-like document navigation
- ✅ Cached JSON tree for repeated queries

### System Flow

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                    │
│  PDF File → PDF Parser → Plain Text → LLM Tree Builder  │
│                              ↓                          │
│                    JSON Tree Index (cached)              │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                     QUERY PIPELINE                       │
│  User Voice/Text → Language Detection → Embed Query     │
│       ↓                                                  │
│  LLM Traverses Tree → Relevant Nodes Selected           │
│       ↓                                                  │
│  Groq LLM → Multilingual Answer → TTS Output            │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
vaani-rag/
├── 📄 app.py                        # Main Streamlit entry point
├── 📄 requirements.txt              # Python dependencies
├── 📄 .env.example                  # Environment variable template
├── 📄 .gitignore                    # Git ignore rules
├── 📄 README.md                     # Project documentation
├── 📄 CHANGELOG.md                  # Version history
├── 📄 CONTRIBUTING.md               # Contribution guidelines
├── 📄 LICENSE # MY License
│
├── 📁 src/
│   ├── 📁 core/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py            # PDF → Text bridge (PyMuPDF)
│   │   ├── tree_builder.py          # Vectorless RAG — JSON Tree
│   │   ├── rag_pipeline.py          # LangChain RAG pipeline
│   │   └── groq_client.py           # Groq API wrapper
│   │
│   ├── 📁 ui/
│   │   ├── __init__.py
│   │   ├── components.py            # Reusable Streamlit components
│   │   └── styles.py                # Custom dark theme CSS
│   │
│   └── 📁 utils/
│       ├── __init__.py
│       ├── language_detector.py     # 6-language auto detection
│       ├── voice_handler.py         # STT (Whisper) + TTS (gTTS)
│       └── logger.py                # Loguru logging setup
│
├── 📁 assets/
│   └── 📁 sample_docs/              # Pre-loaded sample PDF documents
│
├── 📁 tests/
│   ├── test_pdf_parser.py
│   ├── test_tree_builder.py
│   └── test_rag_pipeline.py
│
├── 📁 logs/                         # Auto-generated log files
├── 📁 .cache/trees/                 # Cached JSON tree indexes
└── 📁 .github/
    └── 📁 workflows/
        └── ci.yml                   # GitHub Actions CI pipeline
```

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Groq API Key — [Get it free here](https://console.groq.com)
- `ffmpeg` — Required for audio processing
  ```bash
  # Windows (via Chocolatey)
  choco install ffmpeg

  # macOS
  brew install ffmpeg

  # Ubuntu/Debian
  sudo apt install ffmpeg
  ```

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/ThedRk1607/Vaani-RAG-Multi-Language-Voice-Agent1.git
cd vaani-rag

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and add your GROQ_API_KEY

# 5. Launch the application
streamlit run app.py
```

---

## 🎯 Usage

### Voice Mode
1. Click the **🎤 Record** button in the chat interface
2. Speak your question in any supported language
3. Vaani automatically detects your language
4. Receive a spoken answer in the same language

### Text Mode
1. Type your question in the chat input box
2. Select language manually or leave on **Auto Detect**
3. Get an instant answer sourced from your documents

### PDF Management
- **Runtime Upload** — Drag and drop any PDF in the sidebar
- **Pre-loaded Documents** — Select from the available sample documents
- **Tree View** — Expand the sidebar to see the document's JSON tree structure

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

```env
# Groq API
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-70b-8192

# LLM Settings
MAX_TOKENS=1024
TEMPERATURE=0.1

# RAG Settings
DEFAULT_LANGUAGE=auto
TREE_CACHE_DIR=.cache/trees

# Voice Settings
STT_MODEL=base

# App Settings
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🌍 Supported Languages

| Language | Code | Voice Input | Voice Output |
|----------|------|-------------|--------------|
| English | `en` | ✅ | ✅ |
| Hindi | `hi` | ✅ | ✅ |
| Hinglish | `hi-en` | ✅ | ✅ |
| Bengali | `bn` | ✅ | ✅ |
| Marathi | `mr` | ✅ | ✅ |
| Bhojpuri | `bho` | ✅ | ✅ |

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src tests/

# Run specific test file
pytest tests/test_pdf_parser.py -v
```

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

```bash
# 1. Fork the repository
# 2. Create your feature branch
git checkout -b feature/your-feature-name

# 3. Commit your changes
git commit -m "feat: add your feature description"

# 4. Push to your branch
git push origin feature/your-feature-name

# 5. Open a Pull Request
```

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation update |
| `refactor:` | Code refactor |
| `test:` | Adding tests |
| `chore:` | Maintenance |

---

## 📋 Roadmap

- [x] Vectorless RAG with JSON Tree
- [x] 6 Indian language support
- [x] Voice Input + Output
- [x] PDF runtime upload
- [x] Confidence scoring
- [x] Cache system
- [ ] ElevenLabs TTS integration (English)
- [ ] Vapi voice agent integration
- [ ] Docker support
- [ ] REST API endpoint
- [ ] Support for DOCX, TXT files

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) — Lightning-fast LLM inference
- [LangChain](https://langchain.com) — RAG pipeline framework
- [Streamlit](https://streamlit.io) — Python-native UI framework
- [OpenAI Whisper](https://github.com/openai/whisper) — Accurate multilingual STT
- [PyMuPDF](https://pymupdf.readthedocs.io) — Fast PDF parsing
- [gTTS](https://gtts.readthedocs.io) — Google Text-to-Speech

---

<div align="center">

Built with Ashutosh ❤️ for learning production-grade AI systems

⭐ Star this repo if you found it helpful!

</div>
