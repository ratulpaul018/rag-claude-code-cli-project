"""
Agentic RAG Document Analysis System using LangGraph
Advanced multi-agent retrieval and reasoning for document Q&A
"""

import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Any
import operator

# Configuration
BOOK_PATH = "book.pdf"
OLLAMA_MODEL = "llama3.2:latest"
EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 250
VECTOR_DB_PATH = "./chroma_db"
RETRIEVAL_K = 15


class AgentState(TypedDict):
    """State for the agentic RAG system"""
    question: str
    documents: list
    analysis: str
    answer: str
    reasoning_steps: Annotated[list, operator.add]
    source_documents: list


def load_and_chunk_book(pdf_path: str):
    """Load PDF and split into chunks with document metadata"""
    print(f"Loading document from {pdf_path}...")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Document not found at {pdf_path}")

    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages")

    # Add document filename to metadata
    filename = os.path.basename(pdf_path)
    for doc in documents:
        doc.metadata['source_document'] = filename

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from {filename}")

    return chunks


def create_vector_store(chunks):
    """Create vector store with embeddings"""
    print(f"Creating embeddings using {EMBEDDING_MODEL}...")

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH,
        collection_name="agentic_rag"
    )
    print("Vector store created successfully")
    return vector_store


def load_vector_store():
    """Load existing vector store"""
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vector_store = Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings,
        collection_name="agentic_rag"
    )
    return vector_store


def get_vector_store():
    """Get vector store if it exists, None otherwise"""
    try:
        if not os.path.exists(VECTOR_DB_PATH):
            return None
        return load_vector_store()
    except Exception:
        return None


# Tool definitions for the agent
@tool
def retrieve_documents(query: str, vector_store) -> list:
    """Retrieve relevant documents from the knowledge base"""
    retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_K})
    docs = retriever.invoke(query)
    return docs


@tool
def analyze_context(documents: list) -> str:
    """Analyze retrieved documents to extract key information"""
    if not documents:
        return "No relevant documents found."

    context = "\n\n---\n\n".join([
        f"[Page {doc.metadata.get('page', 'N/A')}] {doc.page_content}"
        for doc in documents
    ])
    return context


def create_agentic_rag_chain(vector_store):
    """Create an agentic RAG chain using LangGraph"""
    print(f"Initializing agentic RAG with {OLLAMA_MODEL}...")

    llm = Ollama(model=OLLAMA_MODEL, temperature=0.7)

    # Define prompts for different stages
    retrieval_prompt = PromptTemplate(
        template="""Analyze this question and determine what information needs to be retrieved from documents:

Question: {question}

Provide a clear retrieval query that will help find the most relevant information.""",
        input_variables=["question"]
    )

    analysis_prompt = PromptTemplate(
        template="""You are an expert document analyst. Analyze the following retrieved information to answer the question.

Question: {question}

Retrieved Information:
{context}

Provide:
1. Key findings from the documents
2. Relevant quotes or data
3. Document sources and page numbers
4. Confidence level in the answer

Analysis:""",
        input_variables=["question", "context"]
    )

    answer_prompt = PromptTemplate(
        template="""Based on your analysis of the documents, provide a comprehensive answer.

Question: {question}

Analysis:
{analysis}

Provide a structured, well-organized answer that:
- Directly addresses the question
- Explains the reasoning
- Highlights key information
- Notes any limitations or uncertainties

If asked by the user to present the answer in a specific format (like bullet points, numbered lists, or tables), make sure to follow that format.

Answer:""",
        input_variables=["question", "analysis"]
    )

    # Define graph nodes
    def retrieve_node(state: AgentState) -> dict:
        """Retrieval node - find relevant documents"""
        question = state["question"]

        # Use LLM to formulate better retrieval query
        retrieval_chain = retrieval_prompt | llm | StrOutputParser()
        search_query = retrieval_chain.invoke({"question": question})

        print(f"Search query: {search_query}")

        # Retrieve documents
        retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_K})
        documents = retriever.invoke(question)

        return {
            "documents": documents,
            "reasoning_steps": [f"Retrieved {len(documents)} relevant documents for query: {search_query}"]
        }

    def analyze_node(state: AgentState) -> dict:
        """Analysis node - analyze retrieved documents"""
        question = state["question"]
        documents = state["documents"]

        # Format context
        context = "\n\n---\n\n".join([
            f"[Page {doc.metadata.get('page', 'N/A')}] {doc.page_content}"
            for doc in documents
        ])

        # Analyze using LLM
        analysis_chain = analysis_prompt | llm | StrOutputParser()
        analysis = analysis_chain.invoke({
            "question": question,
            "context": context
        })

        return {
            "analysis": analysis,
            "source_documents": documents,
            "reasoning_steps": [
                f"Analyzed {len(documents)} documents",
                "Extracted key findings and relevant information",
                "Identified document sources and page references"
            ]
        }

    def answer_node(state: AgentState) -> dict:
        """Answer node - generate final answer"""
        question = state["question"]
        analysis = state["analysis"]

        # Generate final answer
        answer_chain = answer_prompt | llm | StrOutputParser()
        answer = answer_chain.invoke({
            "question": question,
            "analysis": analysis
        })

        return {
            "answer": answer,
            "reasoning_steps": ["Generated comprehensive answer based on analysis"]
        }

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("answer", answer_node)

    # Add edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "analyze")
    workflow.add_edge("analyze", "answer")
    workflow.add_edge("answer", END)

    # Compile the graph
    graph = workflow.compile()

    class AgenticRAGChain:
        def __init__(self, graph):
            self.graph = graph
            self.vector_store = vector_store

        def invoke(self, input_dict):
            """Execute the agentic RAG workflow"""
            question = input_dict.get("query", "")

            # Run the graph
            result = self.graph.invoke({
                "question": question,
                "documents": [],
                "analysis": "",
                "answer": "",
                "reasoning_steps": [],
                "source_documents": []
            })

            # Format source documents
            source_documents = result.get("source_documents", [])

            return {
                "result": result.get("answer", "No answer generated"),
                "source_documents": source_documents,
                "reasoning": result.get("reasoning_steps", []),
                "analysis": result.get("analysis", "")
            }

    return AgenticRAGChain(graph)


def setup_agentic_rag(pdf_path: str):
    """Setup agentic RAG system from scratch"""
    chunks = load_and_chunk_book(pdf_path)
    vector_store = create_vector_store(chunks)
    qa_chain = create_agentic_rag_chain(vector_store)
    return qa_chain


def load_agentic_rag(vector_store_path: str = VECTOR_DB_PATH):
    """Load existing agentic RAG system"""
    if not os.path.exists(vector_store_path):
        raise FileNotFoundError(f"Vector store not found at {vector_store_path}")

    vector_store = load_vector_store()
    qa_chain = create_agentic_rag_chain(vector_store)
    return qa_chain


def answer_question_agentic(qa_chain, question: str):
    """Ask a question using agentic RAG"""
    print(f"\nQuestion: {question}")
    print("-" * 50)

    result = qa_chain.invoke({"query": question})

    print(f"Answer: {result['result']}")

    print("\nReasoning Steps:")
    for i, step in enumerate(result.get('reasoning', []), 1):
        print(f"  {i}. {step}")

    print("\nSource documents:")
    for i, doc in enumerate(result['source_documents'], 1):
        print(f"  {i}. Page {doc.metadata.get('page', 'N/A')}: {doc.page_content[:100]}...")


def main():
    """Main function"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  First time: python agentic_rag_doc_analysis.py setup <path_to_book.pdf>")
        print("  Ask questions: python agentic_rag_doc_analysis.py ask <question>")
        print("\nExample:")
        print("  python agentic_rag_doc_analysis.py setup ./my_book.pdf")
        print("  python agentic_rag_doc_analysis.py ask 'What are the main topics?'")
        return

    command = sys.argv[1]

    if command == "setup":
        if len(sys.argv) < 3:
            print("Error: Please provide path to PDF book")
            print("Usage: python agentic_rag_doc_analysis.py setup <path_to_book.pdf>")
            return

        pdf_path = sys.argv[2]
        qa_chain = setup_agentic_rag(pdf_path)
        print("\n✓ Agentic RAG system ready! You can now ask questions.")

    elif command == "ask":
        if len(sys.argv) < 3:
            print("Error: Please provide a question")
            print("Usage: python agentic_rag_doc_analysis.py ask '<question>'")
            return

        question = " ".join(sys.argv[2:])
        qa_chain = load_agentic_rag()
        answer_question_agentic(qa_chain, question)

    elif command == "interactive":
        qa_chain = load_agentic_rag()
        print("Agentic RAG system loaded. Type 'exit' to quit.\n")

        while True:
            question = input("Question: ").strip()
            if question.lower() == "exit":
                break
            if question:
                answer_question_agentic(qa_chain, question)

    else:
        print(f"Unknown command: {command}")
        print("Use 'setup', 'ask', or 'interactive'")


if __name__ == "__main__":
    main()
