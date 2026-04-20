"""
RAGAS Evaluation for Agentic RAG System
Evaluates multi-step reasoning RAG using RAGAS metrics
"""

import os
import json
from pathlib import Path
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from agentic_rag_doc_analysis import load_agentic_rag, get_vector_store

# Configuration
OLLAMA_MODEL = "llama3.2:latest"
EMBEDDING_MODEL = "nomic-embed-text"
EVALUATION_DATA_FILE = "evaluation_data.json"


def prepare_evaluation_dataset():
    """Load evaluation dataset"""
    if os.path.exists(EVALUATION_DATA_FILE):
        with open(EVALUATION_DATA_FILE, "r") as f:
            data = json.load(f)
            eval_data = data.get("questions", [])
            print(f"Loaded {len(eval_data)} evaluation samples")
            return eval_data
    return []


def generate_responses(qa_chain, questions):
    """Generate answers for evaluation questions"""
    print(f"\nGenerating {len(questions)} responses...")
    responses = []

    for i, item in enumerate(questions, 1):
        question = item.get("question")
        try:
            result = qa_chain.invoke({"query": question})
            answer = result.get("result", "")
            source_docs = result.get("source_documents", [])

            contexts = [doc.page_content for doc in source_docs]

            responses.append({
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": item.get("ground_truth", ""),
            })

            print(f"  [{i}/{len(questions)}] ✓ {question[:50]}...")

        except Exception as e:
            print(f"  [{i}/{len(questions)}] ✗ Error: {str(e)[:50]}")
            continue

    return responses


def evaluate_rag_system(responses):
    """Evaluate Agentic RAG system using RAGAS metrics"""
    if not responses:
        print("No responses to evaluate!")
        return None

    print(f"\nEvaluating {len(responses)} responses with RAGAS...")

    # Create dataset
    eval_dataset = Dataset.from_dict({
        "question": [r["question"] for r in responses],
        "answer": [r["answer"] for r in responses],
        "contexts": [r["contexts"] for r in responses],
        "ground_truth": [r["ground_truth"] for r in responses],
    })

    # Initialize LLM and embeddings for evaluation
    print("Initializing evaluation models...")
    eval_llm = Ollama(model=OLLAMA_MODEL, temperature=0)
    eval_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    try:
        print("Running RAGAS evaluation...")
        # Run evaluation
        results = evaluate(
            eval_dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
            llm=eval_llm,
            embeddings=eval_embeddings,
        )

        return results

    except Exception as e:
        print(f"Evaluation error: {e}")
        return None


def print_evaluation_report(results, responses):
    """Print detailed evaluation report"""
    print("\n" + "=" * 80)
    print("AGENTIC RAG SYSTEM - RAGAS EVALUATION REPORT")
    print("=" * 80)

    if results is None:
        print("Evaluation failed or no results available")
        return

    # Get metric scores
    scores = {
        "faithfulness": results["faithfulness"],
        "answer_relevancy": results["answer_relevancy"],
        "context_precision": results["context_precision"],
        "context_recall": results["context_recall"],
    }

    # Print title
    print("\n[AGENTIC RAG METRICS]")
    print("-" * 80)

    # Print individual scores
    print("\nMetric Scores (0-1, higher is better):")
    print("-" * 80)
    for metric, score in scores.items():
        bar_length = int(score * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        status = "✓" if score > 0.7 else "⚠" if score > 0.5 else "✗"
        print(f"{metric:20} | {bar} | {score:.4f} {status}")

    # Calculate overall score
    overall_score = sum(scores.values()) / len(scores)
    print("-" * 80)
    bar_length = int(overall_score * 50)
    bar = "█" * bar_length + "░" * (50 - bar_length)
    overall_status = "✓ EXCELLENT" if overall_score > 0.8 else "✓ GOOD" if overall_score > 0.7 else "⚠ FAIR" if overall_score > 0.5 else "✗ POOR"
    print(f"{'Overall Score':20} | {bar} | {overall_score:.4f} {overall_status}")

    # Print interpretation
    print("\n[METRIC INTERPRETATION]")
    print("-" * 80)
    print("• Faithfulness: Answer is grounded in retrieved context (no hallucinations)")
    print("• Answer Relevancy: Answer directly addresses the question")
    print("• Context Precision: Retrieved documents are relevant to the question")
    print("• Context Recall: All relevant information is retrieved from documents")

    print("\n[SCORE RANGES]")
    print("-" * 80)
    print("  0.0 - 0.3: ✗ Poor      (Needs significant improvement)")
    print("  0.3 - 0.6: ⚠ Fair      (Acceptable, room for improvement)")
    print("  0.6 - 0.8: ✓ Good      (Well-functioning system)")
    print("  0.8 - 1.0: ✓ Excellent (High-quality results)")

    # Detailed recommendations
    print("\n[RECOMMENDATIONS FOR IMPROVEMENT]")
    print("-" * 80)

    improvements = []
    if scores["faithfulness"] < 0.7:
        improvements.append("FAITHFULNESS: Add constraints like 'Answer only from context'")
    if scores["answer_relevancy"] < 0.7:
        improvements.append("ANSWER RELEVANCY: Improve prompt to emphasize question focus")
    if scores["context_precision"] < 0.7:
        improvements.append("CONTEXT PRECISION: Increase RETRIEVAL_K for better filtering")
    if scores["context_recall"] < 0.7:
        improvements.append("CONTEXT RECALL: Increase RETRIEVAL_K or reduce CHUNK_SIZE")

    if improvements:
        for i, rec in enumerate(improvements, 1):
            print(f"{i}. {rec}")
    else:
        print("✓ No major improvements needed! System is performing well.")

    # System characteristics for Agentic RAG
    print("\n[AGENTIC RAG CHARACTERISTICS]")
    print("-" * 80)
    print(f"• Multi-stage reasoning: ✓ Enabled")
    print(f"• Responses evaluated: {len(responses)} questions")
    print(f"• Average answer length: {sum(len(r['answer'].split()) for r in responses) // len(responses)} words")
    print(f"• Average context chunks: {sum(len(r['contexts']) for r in responses) // len(responses)} chunks")

    # Save results
    report_file = "evaluation_report.json"
    with open(report_file, "w") as f:
        json.dump({
            "system": "Agentic RAG",
            "scores": scores,
            "overall_score": overall_score,
            "responses_count": len(responses),
            "timestamp": str(__import__('datetime').datetime.now())
        }, f, indent=2)
    print(f"\n✓ Report saved to: {report_file}")

    print("=" * 80)


def create_sample_evaluation_data():
    """Create sample evaluation data"""
    sample_data = {
        "questions": [
            {
                "question": "What is the main topic of the document?",
                "ground_truth": "The document's primary subject matter and focus."
            },
            {
                "question": "What are the key findings or conclusions?",
                "ground_truth": "Important results, conclusions, and main points discussed."
            },
            {
                "question": "Who authored this document?",
                "ground_truth": "The author or creator information."
            }
        ]
    }
    with open(EVALUATION_DATA_FILE, "w") as f:
        json.dump(sample_data, f, indent=2)
    print(f"✓ Sample {EVALUATION_DATA_FILE} created")


def main():
    """Main evaluation workflow"""
    print("[AGENTIC RAG] RAGAS Evaluation Tool")
    print("-" * 80)

    # Check if vector store exists
    try:
        vector_store = get_vector_store()
        if vector_store is None:
            print("✗ No indexed documents found.")
            print("Please upload documents first using the web app or CLI.")
            return
        print("✓ Vector store found")
    except Exception as e:
        print(f"✗ Error accessing vector store: {e}")
        print("Please upload documents and try again.")
        return

    # Prepare evaluation dataset
    eval_data = prepare_evaluation_dataset()
    if not eval_data:
        print(f"\n✗ No {EVALUATION_DATA_FILE} found")
        create_sample_evaluation_data()
        print(f"Please edit {EVALUATION_DATA_FILE} with your test questions and run again.")
        return

    questions = eval_data
    if not questions:
        print(f"✗ No questions found in {EVALUATION_DATA_FILE}")
        return

    # Load RAG chain
    print("\nLoading Agentic RAG system...")
    try:
        qa_chain = load_agentic_rag()
        print("✓ Agentic RAG loaded")
    except Exception as e:
        print(f"✗ Error loading RAG: {e}")
        return

    # Generate responses
    responses = generate_responses(qa_chain, questions)
    if not responses:
        print("✗ Failed to generate responses")
        return

    print(f"✓ Generated {len(responses)} responses")

    # Evaluate
    results = evaluate_rag_system(responses)

    # Print report
    print_evaluation_report(results, responses)


if __name__ == "__main__":
    main()
