# CLAUDE.md - Book QA Project Guidelines

## Project: Local-RAG Book Question Answering System

A private, local-first RAG (Retrieval-Augmented Generation) system using LangChain, Ollama, and ChromaDB for intelligent document analysis and Q&A.

## System Architecture

```
PDF Upload → Chunking (500 chars, 150 overlap)
    ↓
Embeddings (nomic-embed-text)
    ↓
ChromaDB Vector Store (./chroma_db)
    ↓
Retrieval (Top K=5)
    ↓
LLM (llama3.2:latest) → Structured Response
```

## Core Files

| File                   | Purpose                                                                |
| ---------------------- | ---------------------------------------------------------------------- |
| `book_qa.py`           | Core RAG logic: PDF loading, chunking, embeddings, chain creation      |
| `web_app.py`           | Flask REST API for web interface (/api/upload, /api/ask, /api/get-pdf) |
| `templates/index.html` | Web UI structure (dark theme, two-column layout)                       |
| `static/script.js`     | Frontend logic (upload, Q&A, PDF modal navigation)                     |
| `static/style.css`     | Styling (dark mode, scrollable PDFs, chat messages)                    |

## Configuration (book_qa.py)

```python
OLLAMA_MODEL = "llama3.2:latest"      # LLM for answer generation
EMBEDDING_MODEL = "nomic-embed-text"  # Embedding model
CHUNK_SIZE = 500                       # Characters per chunk
CHUNK_OVERLAP = 150                    # Overlap between chunks
VECTOR_DB_PATH = "./chroma_db"        # Persistent vector store
RETRIEVAL_K = 5                        # Top K documents to retrieve
```

## Build/Execution Commands

### **Web Interface (Recommended)**

```bash
cd "c:/RAG venv (09.04.2026)/ragenv"
python web_app.py
# Open: http://localhost:5000
```

### **CLI Interface**

```bash
# First time: Setup with PDF
python book_qa.py setup path/to/book.pdf

# Ask single question
python book_qa.py ask "What is the main topic?"

# Interactive mode
python book_qa.py interactive
```

### **Environment Setup**

```bash
pip install flask langchain langchain-community chromadb sentence-transformers transformers pypdf werkzeug
ollama pull llama3.2:latest
```

## Code Style & Standards

- **Naming:** Use `snake_case` for functions/variables, `PascalCase` for classes
- **Typing:** All function signatures must include type hints
- **Frameworks:** Use **LCEL (LangChain Expression Language)** for chain construction
- **LLM Config:** Use `Ollama` class; always verify model is pulled before use
- **Error Handling:** Explicit checks for file existence and directories
- **Documentation:** Google-style docstrings for all functions
- **Comments:** Only add comments for non-obvious logic

## Architectural Patterns

- **RAG Flow:** Load PDF → Split Chunks → Generate Embeddings → Store in Chroma → Retrieve Top-K → Generate Answer
- **Prompt Template:** Instructs LLM to format output with paragraphs, bullet points, tables, bold text
- **RAGChain Wrapper:** Custom class that returns both answer AND source documents with page numbers
- **Vector Store Persistence:** ChromaDB saves embeddings to disk; load existing store on app restart
- **PDF Serving:** Flask endpoint `/api/get-pdf/<filename>` serves PDFs for modal viewer

## Web Interface Features

✅ **Upload Section (Left Column)**

- Drag & drop or click to upload PDFs
- Multiple books support with indexed list
- File status indicators (uploading, processing, complete)

✅ **Q&A Section (Right Column)**

- Chat-style message display
- Auto-scroll on new messages
- Black-shaded messages with colored accents

✅ **References Section (Full Width)**

- Clickable page numbers
- PDF modal viewer with page navigation
- Scrollable full-page PDF display
- Previous/Next page buttons

## Known Issues & Solutions

| Issue                             | Solution                                                        |
| --------------------------------- | --------------------------------------------------------------- |
| PDF top is cut off in modal       | CSS: Changed `align-items: center` to `align-items: flex-start` |
| Ollama 404 error                  | Run: `ollama pull llama3.2:latest` before starting app          |
| File not found on reference click | Use returned filename from upload response, not original        |
| Empty uploads folder              | Run reset endpoint to clear localStorage + uploads              |

## Development Guidelines

### When Adding New Features

1. Don't add features beyond what was requested
2. Prefer editing existing files over creating new ones
3. Keep implementation minimal—no premature abstractions
4. Test in the web interface before marking as complete

### When Modifying Code

1. Read the file first before making changes
2. Update both backend (Python) and frontend (JS) when needed
3. Always test the UI/UX impact
4. Don't add error handling for impossible scenarios

### Git & Version Control

- Create descriptive commits when requested
- Include "Co-Authored-By: Claude Haiku 4.5" in commits
- Don't force-push unless explicitly authorized
- Test before committing
