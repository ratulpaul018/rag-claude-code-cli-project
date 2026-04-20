# Claude Configuration for DOC_QA_AG_RAG

## Project Overview

**DOC_QA_AG_RAG** is an Agentic RAG (Retrieval-Augmented Generation) document analysis system using LangGraph for intelligent multi-step reasoning. This is an improved version of the basic document analysis system (book_qa.py in Book QA Project) with deeper analysis capabilities.

## System Architecture

### Three-Stage Agentic Workflow

```
User Question
    ↓
[Stage 1] Retrieval Agent
  - Analyzes question
  - Formulates optimal queries
  - Retrieves relevant context
    ↓
[Stage 2] Analysis Agent
  - Examines retrieved chunks
  - Extracts key information
  - Identifies patterns
    ↓
[Stage 3] Answer Agent
  - Synthesizes findings
  - Adds reasoning steps
  - Generates final answer
    ↓
Answer with Citations
```

### Tech Stack

- **Framework**: Flask (HTTP server)
- **RAG Engine**: LangChain + LangGraph
- **Vector Store**: ChromaDB (persistent)
- **PDF Processing**: PyMuPDFLoader
- **LLM**: Ollama (local inference)
- **Embeddings**: nomic-embed-text
- **Frontend**: Vanilla JS, CSS Grid, PDF.js

## File Structure & Roles

### Core Files

| File                          | Purpose                                                                  |
| ----------------------------- | ------------------------------------------------------------------------ |
| `web_app_up.py`               | Flask server with auto-loading - HTTP endpoints, file uploads, questions |
| `agentic_rag_doc_analysis.py` | LangGraph agentic RAG logic - multi-stage reasoning                      |
| `static/script_up.js`         | Frontend - chat, PDF viewer, suggested questions, source interaction    |
| `static/style_up.css`         | Styling - responsive grid, cards, animations                            |
| `templates/index_up.html`     | Web UI - layout, chat interface, suggested questions, modal              |
| `README.md`                   | User documentation                                                       |
| `CLAUDE.md`                   | This file - development context                                         |

### Auto-Generated Folders

| Folder      | Purpose                                  |
| ----------- | ---------------------------------------- |
| `uploads/`  | Temporary PDF storage                    |
| `chroma_db/` | Vector database (persistent, auto-loads) |

## Key Concepts

### Agentic vs Basic RAG

| Aspect        | Basic (book_qa.py)     | Agentic (this)                    |
| ------------- | ---------------------- | --------------------------------- |
| **Workflow**  | Retrieval → Generation | Retrieval → Analysis → Generation |
| **Reasoning** | Direct                 | Multi-step with logic             |
| **Speed**     | 2-3 sec                | 8-15 sec                          |
| **Accuracy**  | Good                   | Better                            |
| **Best For**  | Simple Q&A             | Complex analysis                  |

### Important Parameters (agentic_rag_doc_analysis.py)

```python
CHUNK_SIZE = 900           # Balance: larger = more context, smaller = precision
CHUNK_OVERLAP = 250        # Smooth transitions between chunks
RETRIEVAL_K = 15           # Increase for more context, decrease for speed
```

Tuning guide:

- **Low accuracy?** Increase RETRIEVAL_K (15 → 30)
- **Slow responses?** Decrease RETRIEVAL_K (15 → 5)
- **Missing citations?** Increase CHUNK_OVERLAP (250 → 500)

## API Endpoints

### POST /api/upload

- **Purpose**: Upload and index PDF documents
- **Request**: multipart/form-data with 'file' field
- **Response**: `{ success, filename, chunks, message, suggested_questions[] }`
- **Logic**: Loads PDF → chunks → embeddings → ChromaDB → generates AI questions
- **New Feature**: Generates 4 suggested questions using Ollama LLM from document chunks (temperature=0.5)

### POST /api/ask

- **Purpose**: Query indexed documents
- **Request**: `{ question: string }`
- **Response**: `{ success, answer, sources[], follow_up }`
- **Logic**: Invokes agentic chain (3-stage workflow)
- **New Feature**: Includes follow-up message "❓ What more can I help you with?" after each answer

### GET /api/status

- **Purpose**: Check system readiness
- **Response**: `{ vector_store_loaded, qa_chain_ready }`

### POST /api/reset

- **Purpose**: Clear all data
- **Logic**: Deletes uploads/ and chroma_db/ directories

### Auto-Loading on Startup

- **Purpose**: Load persisted vector store when Flask starts
- **Implementation**: `load_existing_on_startup()` function in web_app_up.py
- **Benefit**: Users don't need to re-upload PDFs after Flask restarts
- **Impact**: Vector store is immediately available without waiting for on-demand loading

## Frontend Architecture

### Key Variables (script.js)

```javascript
selectedFile; // Currently selected PDF
qa_chain; // Backend RAG chain state
vector_store_loaded; // DB readiness flag
currentPdfFile; // File being viewed in modal
currentPdfPage; // Current page in PDF viewer
```

### Key Functions

| Function                  | Purpose                |
| ------------------------- | ---------------------- |
| `handleFileSelect()`      | File picker handler    |
| `processFile()`           | Upload & index PDF     |
| `askQuestion()`           | Send Q to backend      |
| `displaySources()`        | Show reference cards   |
| `openPdfPage()`           | Open PDF modal at page |
| `loadAndDisplayPdfPage()` | Render PDF pages       |

### UI Components

- **Upload Section**: Drag-drop, file info
- **Chat Section**: Messages, input, send button
- **Sources Section**: Grid of reference cards
- **PDF Modal**: Full-page PDF viewer with navigation

## Development Workflow

### Adding Features

1. **Backend changes**: Modify `agentic_rag_doc_analysis.py`
   - Update prompts in `create_agentic_rag_chain()`
   - Adjust retrieval in `invoke()` method

2. **Frontend changes**: Modify `static/script.js`
   - Update API calls in `askQuestion()`
   - Enhance UI in `displaySources()`

3. **Styling changes**: Modify `static/style.css`
   - Use CSS Grid for responsive layouts
   - Follow color scheme: #06b6d4 (cyan), #334155 (gray)

### Testing

**Manual Testing**:

```bash
# Make sure Ollama is running first
ollama serve

# In another terminal
python web_app_up.py
# Open http://127.0.0.1:7000
# Upload PDF → View suggested questions → Ask questions → Check responses
```

**Quick Test**:

- Upload 5-10 page PDF
- Verify suggested questions appear automatically (generated by Ollama)
- Click a suggested question to test it
- Ask a custom question
- Verify follow-up message appears after answer
- Click source references to view PDF pages
- Check response time (8-15 sec expected for complex questions)

## Important Constraints

### ❌ DO NOT

- Change ALLOWED_EXTENSIONS from {'pdf'} (security)
- Use external APIs for embeddings (should be local Ollama)
- Store sensitive data in uploads/ (temporary only)
- Modify vector store path without updating everywhere
- Skip document metadata in sources

### ✅ DO

- Keep Ollama running on localhost:11434
- Validate question input (non-empty)
- Handle errors gracefully with user messages
- Test before pushing to main
- Document any new parameters in README.md

## Recent Updates (April 20, 2026)

### Auto-Loading Vector Store on Startup
- **Problem**: Flask restarts would lose the qa_chain global variable, requiring users to re-upload PDFs
- **Solution**: Added `load_existing_on_startup()` function that automatically loads persisted vector store
- **Impact**: Vector store is immediately available after Flask starts, no user action needed
- **Code**: In web_app_up.py, called during Flask app initialization

### Ollama-Based Suggested Questions
- **Feature**: AI-generated questions appear immediately after PDF upload
- **Implementation**: `generate_suggested_questions(chunks)` uses LangChain + Ollama chain
- **Details**:
  - Extracts context from first 6 document chunks
  - Uses PromptTemplate to request exactly 4 specific questions
  - Temperature set to 0.5 for balanced quality
  - Returns up to 4 questions, filters out duplicates and short questions
- **Code**: In web_app_up.py, lines 45-93

### Professional Follow-Up Message
- **Feature**: After each answer, system displays "❓ What more can I help you with?"
- **Purpose**: Encourages continued interaction and engagement
- **Implementation**: Added 'follow_up' field to /api/ask response
- **Code**: In web_app_up.py, line 185

## Common Issues & Solutions

### Issue: Slow Responses (>20 sec)

**Cause**: LangGraph agents over-reasoning
**Solutions**:

- Reduce RETRIEVAL_K from 15 to 10
- Simplify prompt template in agentic_rag_doc_analysis.py
- Check Ollama CPU threads: `ollama run llama3.2:latest`

### Issue: Low Quality Answers

**Cause**: Poor chunk boundaries or retrieval
**Solutions**:

- Increase RETRIEVAL_K from 15 to 20-30
- Reduce CHUNK_SIZE from 900 to 700
- Check document quality (clear text, not scanned images)

### Issue: References Not Showing

**Cause**: Source documents not in result
**Solutions**:

- Check `source_documents` in API response
- Verify ChromaDB contains documents: check `chroma_db/` directory
- Increase RETRIEVAL_K to ensure chunks retrieved
- Ensure vector store was properly indexed after upload

### Issue: PDF Pages Not Loading

**Cause**: PDF.js path issue or corrupt PDF
**Solutions**:

- Check browser console for errors
- Verify PDF is valid (try opening in Adobe)
- Check CORS headers in Flask (should be fine for local)

## Performance Targets

| Metric             | Target    | Current      |
| ------------------ | --------- | ------------ |
| Upload 10-page PDF | <5 sec    | 2-3 sec ✅   |
| Process embeddings | 20 sec    | 15-20 sec ✅ |
| Simple question    | <10 sec   | 5-8 sec ✅   |
| Complex question   | 15-20 sec | 10-15 sec ✅ |

## Git Workflow

**Branch**: main
**Commits**: Use descriptive messages with Co-Authored-By footer
**Push**: Only tested, working code

Example commit:

```
Update: Improve agentic reasoning with better prompt

- Enhanced analysis agent prompt for clarity
- Increased RETRIEVAL_K default from 15 to 20
- Added timeout handling for LangGraph state

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

## Comparison with Sibling Projects

### book_qa.py (Basic RAG)

- Same static/templates files
- Simpler agentic_rag_doc_analysis.py
- Faster responses (2-3 sec)
- Less reasoning

### multi_doc_rag.py

- Separate vector stores per document
- Document awareness in retrieval
- Same speed as basic RAG
- Good for multi-document comparison

### This Project (Agentic RAG)

- Complex multi-stage reasoning
- Single unified document space
- Slower but smarter answers
- Best for analytical questions

## Configuration Files

### .env (Optional)

```bash
OLLAMA_MODEL=llama3.2:latest
EMBEDDING_MODEL=nomic-embed-text
FLASK_ENV=development
```

### requirements.txt (Parent Directory)

All dependencies installed from parent `requirements.txt`

## Next Steps for Enhancement

### Completed (April 20, 2026)
✅ **Auto-loading vector store** - Persists across Flask restarts
✅ **Ollama-based suggested questions** - AI-generated after upload
✅ **Professional follow-up messages** - Encourages continued interaction

### Potential Improvements
1. **Add conversation memory**: Keep chat history across sessions
2. **Implement streaming**: Stream answers as generated for better UX
3. **Add document filtering**: Search within specific PDFs only
4. **Optimize LangGraph**: Use conditional edges for faster reasoning paths
5. **Add RAGAS evaluation**: Measure answer quality with automated metrics
6. **Multi-document support**: Index multiple PDFs separately with awareness
7. **User authentication**: Track user sessions and preferences

## Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Ollama**: http://127.0.0.1:11434 (must be running)
- **ChromaDB**: Persistent at ./chroma_db/
- **Flask Server**: http://127.0.0.1:7000

## Quick Commands

```bash
# Make sure Ollama is running (in one terminal)
ollama serve

# Run server (in another terminal)
python web_app_up.py

# Check status
curl -s http://127.0.0.1:7000/api/status | python -m json.tool

# Test API
curl -X POST http://127.0.0.1:7000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"test"}'

# Kill process on port 7000 (Windows)
taskkill /F /IM python.exe  # or find and kill specific process

# Clear data (fresh start)
rm -rf uploads/ chroma_db/
```

---

**Last Updated**: 2026-04-20
**Version**: 1.1 (Agentic RAG with Auto-Loading, Suggested Questions, Follow-up)
**Status**: ✅ Production Ready
**Key Changes**:
- Auto-loads vector store on Flask startup
- Ollama-based suggested questions
- Professional follow-up messages
- Fixed qa_chain persistence issue
