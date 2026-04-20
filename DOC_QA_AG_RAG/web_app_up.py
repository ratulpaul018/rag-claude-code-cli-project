from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import json
from werkzeug.utils import secure_filename

# Set the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

print("[AGENTIC RAG] Using Agentic RAG System with LangGraph")
from agentic_rag_doc_analysis import create_agentic_rag_chain as create_rag_chain
from agentic_rag_doc_analysis import load_agentic_rag as load_vector_store_func
from agentic_rag_doc_analysis import create_vector_store, load_and_chunk_book

TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
print(f"[DEBUG] TEMPLATE_FOLDER: {TEMPLATE_FOLDER}")
print(f"[DEBUG] Using local DOC_QA_AG_RAG templates")

app = Flask(__name__,
            template_folder=TEMPLATE_FOLDER,
            static_folder=STATIC_FOLDER)
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Reload templates on every request
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.jinja_env.cache = None  # Disable Jinja2 template cache

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global QA chain
qa_chain = None
vector_store_loaded = False
document_chunks = None

ALLOWED_EXTENSIONS = {'pdf'}

# Try to load existing vector store on startup
def load_existing_on_startup():
    global qa_chain, vector_store_loaded
    try:
        print("[STARTUP] Attempting to load existing vector store...")
        qa_chain = load_vector_store_func()
        vector_store_loaded = True
        print("[STARTUP] Successfully loaded existing vector store")
        return True
    except Exception as e:
        print(f"[STARTUP] No existing vector store found: {e}")
        return False

# Auto-load on Flask startup
load_existing_on_startup()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_suggested_questions(chunks):
    """Generate 4 suggested questions using Ollama from document chunks"""
    try:
        if not chunks or len(chunks) == 0:
            return []

        from langchain_community.llms import Ollama
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        # Extract context from first 6 chunks
        doc_context = "\n\n".join([
            f"[Chunk {i+1}] {chunk.page_content[:300]}"
            for i, chunk in enumerate(chunks[:6])
        ])

        # Create Ollama LLM instance
        llm = Ollama(model="llama3.2:latest", temperature=0.5)

        # Prompt template for generating questions
        question_prompt = PromptTemplate(
            template="""Based on the following document content, generate exactly 4 specific, meaningful, and professional questions that a user might ask about this document.

Document Content:
{content}

Requirements:
- Generate exactly 4 questions
- Each question must be specific and answerable from the document
- Questions should be professional and clear
- One question per line
- No numbering or bullet points
- No introduction text, just the questions

Questions:""",
            input_variables=["content"]
        )

        # Create chain and generate questions
        question_chain = question_prompt | llm | StrOutputParser()
        response = question_chain.invoke({"content": doc_context})

        # Parse response into list of questions
        questions = [q.strip() for q in response.split('\n') if q.strip() and len(q.strip()) > 10]

        return questions[:4]
    except Exception as e:
        print(f"Error generating questions with Ollama: {e}")
        return []


@app.route('/')
def index():
    global vector_store_loaded
    return render_template('index_up.html', vector_store_exists=vector_store_loaded)


@app.route('/api/upload', methods=['POST'])
def upload_book():
    global qa_chain, vector_store_loaded, document_chunks

    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400

        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"Saved file: {filename}")

        print("Loading and chunking the uploaded PDF...")
        chunks = load_and_chunk_book(filepath)
        document_chunks = chunks

        # Create single unified vector store
        vector_store = create_vector_store(chunks)
        print(f"Created unified vector store with {len(chunks)} total chunks")

        print(f"[DEBUG] Before creating RAG chain: qa_chain = {qa_chain}")
        qa_chain = create_rag_chain(vector_store)
        print(f"[DEBUG] After creating RAG chain: qa_chain = {qa_chain}, type = {type(qa_chain)}")
        vector_store_loaded = True

        print("Generating suggested questions...")
        suggested_questions = generate_suggested_questions(chunks)

        return jsonify({
            'success': True,
            'message': f'Successfully processed {filename}. All documents merged and indexed.',
            'chunks': len(chunks),
            'filename': filename,
            'mode': 'agentic',
            'suggested_questions': suggested_questions
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ask', methods=['POST'])
def ask_question():
    global qa_chain

    try:
        if qa_chain is None:
            return jsonify({
                'success': False,
                'error': 'No book loaded. Please upload a PDF first.'
            }), 400

        data = request.json
        question = data.get('question', '').strip()

        if not question:
            return jsonify({'success': False, 'error': 'Question cannot be empty'}), 400

        # Get answer
        result = qa_chain.invoke({"query": question})

        # Format source documents
        sources = []
        if 'source_documents' in result:
            for doc in result['source_documents']:
                sources.append({
                    'page': doc.metadata.get('page', 'N/A'),
                    'content': doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content
                })

        return jsonify({
            'success': True,
            'answer': result['result'],
            'sources': sources,
            'mode': 'agentic',
            'follow_up': '❓ What more can I help you with?'
        })

    except Exception as e:
        error_msg = str(e)
        if 'llama runner process has terminated' in error_msg or 'Ollama call failed' in error_msg:
            return jsonify({
                'success': False,
                'error': 'Ollama service crashed. Please restart Ollama by running: ollama serve'
            }), 503
        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    global vector_store_loaded
    return jsonify({
        'vector_store_loaded': vector_store_loaded,
        'qa_chain_ready': qa_chain is not None
    })


@app.route('/api/get-pdf/<filename>')
def get_pdf(filename):
    """Serve uploaded PDF files"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path) and filename.endswith('.pdf'):
            return send_file(file_path, mimetype='application/pdf')
        return {"error": "File not found"}, 404
    except Exception as e:
        return {"error": str(e)}, 500


@app.route('/api/reset', methods=['POST'])
def reset():
    global qa_chain, vector_store_loaded
    try:
        import shutil

        qa_chain = None
        vector_store_loaded = False

        # Clear uploads folder
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for file in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(f"Cleared uploads folder")

        # Clear all vector store databases (check multiple possible paths)
        vector_store_paths = [
            './chroma_db_agentic',
            '../chroma_db',
            '../chroma_db_active',
            '../chroma_db_multi'
        ]

        for vector_store_path in vector_store_paths:
            if os.path.exists(vector_store_path):
                shutil.rmtree(vector_store_path)
                print(f"Cleared vector store at {vector_store_path}")

        return jsonify({'success': True, 'message': 'System reset - All databases and uploads cleared. Ready for new documents.', 'mode': 'agentic'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/load-existing', methods=['POST'])
def load_existing():
    """Load existing vector store"""
    global qa_chain, vector_store_loaded
    try:
        # For agentic RAG, load_agentic_rag returns the chain directly
        qa_chain = load_vector_store_func()
        vector_store_loaded = True
        return jsonify({'success': True, 'message': 'Loaded existing vector store using Agentic RAG'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, port=7000)
