# Agentic RAG Evaluation Process

## Overview

This document describes how to evaluate the DOC_QA_AG_RAG (Agentic RAG) system using RAGAS metrics.

## What is RAGAS?

**RAGAS** (Retrieval-Augmented Generation Assessment) is a framework for evaluating RAG systems with four key metrics:

1. **Faithfulness** - Is the answer grounded in the retrieved context?
2. **Answer Relevancy** - Does the answer address the question?
3. **Context Precision** - Are the retrieved documents relevant?
4. **Context Recall** - Is all relevant information retrieved?

Each metric scores 0-1 (higher is better).

---

## Setup

### 1. Dependencies

All dependencies are in `requirements.txt`, including RAGAS:

```bash
pip install -r requirements.txt
```

Key packages:
- `ragas==0.1.13` - Evaluation framework
- `langchain`, `langgraph` - RAG system
- `datasets` - Dataset handling

### 2. Evaluation Data

Edit `evaluation_data.json` with your test questions:

```json
{
  "questions": [
    {
      "question": "What is the main topic of this document?",
      "ground_truth": "The primary subject matter discussed."
    },
    {
      "question": "What are the key findings?",
      "ground_truth": "Important conclusions and results."
    }
  ]
}
```

### 3. Upload Documents

Start the web server and upload PDFs:

```bash
python web_app.py
# Open http://localhost:5000
# Upload your PDF documents
```

---

## Running Evaluation

### Quick Start

```bash
python rag_evaluator.py
```

### What Happens

1. **Loads your documents** from `chroma_db_agentic/`
2. **Generates answers** for each question in `evaluation_data.json`
3. **Evaluates** using RAGAS metrics
4. **Reports** scores and recommendations
5. **Saves** results to `evaluation_report.json`

### Expected Output

```
[AGENTIC RAG] RAGAS Evaluation Tool
--------

✓ Vector store found

Loading Agentic RAG system...
✓ Agentic RAG loaded

Generating 3 responses...
  [1/3] ✓ What is the main topic?...
  [2/3] ✓ What are the key findings?...
  [3/3] ✓ What methodologies are used?...
✓ Generated 3 responses

Evaluating 3 responses with RAGAS...
Initializing evaluation models...
Running RAGAS evaluation...

================================================================================
AGENTIC RAG SYSTEM - RAGAS EVALUATION REPORT
================================================================================

[AGENTIC METRICS]
--------

Metric Scores (0-1, higher is better):
--------
faithfulness        | ████████████████████░░░░░░░░░░░░░░░░░░░░ | 0.7234 ✓
answer_relevancy    | █████████████████████░░░░░░░░░░░░░░░░░░░ | 0.7512 ✓
context_precision   | ██████████████████░░░░░░░░░░░░░░░░░░░░░░ | 0.6856 ✓
context_recall      | ███████████████████░░░░░░░░░░░░░░░░░░░░░ | 0.7145 ✓
--------
Overall Score       | ████████████████████░░░░░░░░░░░░░░░░░░░░ | 0.7187 ✓ GOOD

[METRIC INTERPRETATION]
...

✓ Report saved to: evaluation_report.json
```

---

## Understanding Scores

### Score Ranges

| Range | Rating | Meaning |
|-------|--------|---------|
| 0.0 - 0.3 | ✗ Poor | Needs significant improvement |
| 0.3 - 0.6 | ⚠ Fair | Acceptable, room for improvement |
| 0.6 - 0.8 | ✓ Good | Well-functioning system |
| 0.8 - 1.0 | ✓ Excellent | High-quality results |

### Agentic RAG Expectations

For Agentic RAG systems, typical scores are:

| Metric | Target | Notes |
|--------|--------|-------|
| Faithfulness | 0.70+ | Multi-step reasoning can add detail |
| Answer Relevancy | 0.75+ | Should directly address questions |
| Context Precision | 0.65+ | Multi-retrieval may be less precise |
| Context Recall | 0.70+ | Should retrieve comprehensive context |
| **Overall** | **0.70+** | Good agentic system |

---

## Metric Details

### 1. Faithfulness (0-1)

**What it measures**: Is the answer based on retrieved context?

**Good score** (0.7+):
- Answer stays within document boundaries
- No hallucinations or made-up facts
- Citations are accurate

**Low score** (<0.5):
- Answers go beyond context
- Unfounded claims
- Missing or wrong citations

**How to improve**:
- Add prompt: "Answer only from the provided context"
- Increase RETRIEVAL_K to get more context
- Reduce TEMPERATURE from 0.7 to 0.3

### 2. Answer Relevancy (0-1)

**What it measures**: Does the answer address the question?

**Good score** (0.7+):
- Directly answers what was asked
- Relevant to question topic
- No off-topic information

**Low score** (<0.5):
- Answers different question
- Discusses unrelated topics
- Incomplete coverage

**How to improve**:
- Clarify question in prompt
- Add "Focus on [topic]"
- Increase RETRIEVAL_K for better matches

### 3. Context Precision (0-1)

**What it measures**: Are retrieved chunks relevant?

**Good score** (0.7+):
- All retrieved chunks are relevant
- No noise or off-topic chunks
- Direct match to question

**Low score** (<0.5):
- Many irrelevant chunks retrieved
- Poor semantic matching
- Wrong context included

**How to improve**:
- Tune embedding model (try different embeddings)
- Adjust CHUNK_SIZE (try 600-1200)
- Increase retrieval threshold filtering

### 4. Context Recall (0-1)

**What it measures**: Is all relevant context retrieved?

**Good score** (0.7+):
- All relevant information found
- Comprehensive coverage
- Complete context

**Low score** (<0.5):
- Missing important context
- Incomplete information
- Not finding all relevant chunks

**How to improve**:
- **Increase RETRIEVAL_K**: From 15 to 20-30
- Reduce CHUNK_SIZE for more granularity
- Improve document chunking strategy

---

## Practical Examples

### Example 1: Low Faithfulness (0.35)

**Problem**: Answers contain information not in documents

**Symptoms**:
```
Question: "What year was this published?"
Document: Has no publication date
Answer: "Published in 2024"
```

**Solution**:
```python
# Update prompt in agentic_rag_doc_analysis.py
answer_prompt = PromptTemplate(
    template="""Answer ONLY using the provided context. 
If information is not in the context, say "not found in documents".
...
```

### Example 2: Low Answer Relevancy (0.42)

**Problem**: Answers don't address the question

**Symptoms**:
```
Question: "What is the methodology?"
Answer: "The document discusses important topics including..."
(Answer talks about document in general, not methodology)
```

**Solution**:
```python
# Improve retrieval query
retrieval_prompt = PromptTemplate(
    template="""Extract key terms from the question.
Question: {question}

Search terms: methodology, methods, approach, procedure, framework
...
```

### Example 3: Low Context Precision (0.55)

**Problem**: Retrieved chunks not quite right

**Symptoms**:
```
Question: "What is machine learning?"
Retrieved: Chunks about general AI, neural networks, deep learning
(Some relevant, some tangential)
```

**Solution**:
```python
# In agentic_rag_doc_analysis.py
RETRIEVAL_K = 20           # Retrieve more, filter better
CHUNK_SIZE = 700           # Smaller chunks = more precise

# Or use hybrid search combining keyword + semantic
```

### Example 4: Low Context Recall (0.60)

**Problem**: Missing some relevant information

**Symptoms**:
```
Question: "Compare all three approaches"
Retrieved: Information about 2 out of 3 approaches
(Missing one perspective)
```

**Solution**:
```python
RETRIEVAL_K = 30           # Increase from 15 to 30
CHUNK_OVERLAP = 400        # Increase from 250 to 400
```

---

## Optimization Strategies

### For Overall Quality (Target: 0.75+)

```python
# In agentic_rag_doc_analysis.py
CHUNK_SIZE = 900           # Medium: balanced
CHUNK_OVERLAP = 250        # Standard overlap
RETRIEVAL_K = 20           # Increase retrieval
TEMPERATURE = 0.6          # More focused reasoning
```

### For Speed (Trade-off: Lower quality)

```python
CHUNK_SIZE = 600           # Smaller
CHUNK_OVERLAP = 100        # Minimal
RETRIEVAL_K = 10           # Fewer chunks
TEMPERATURE = 0.3          # Fast convergence
```

### For Accuracy (Trade-off: Slower)

```python
CHUNK_SIZE = 1200          # Larger context
CHUNK_OVERLAP = 400        # More overlap
RETRIEVAL_K = 30           # Comprehensive search
TEMPERATURE = 0.8          # Deep reasoning
```

---

## Iterative Improvement Workflow

### Step 1: Baseline Evaluation
```bash
python rag_evaluator.py
# Record scores in a spreadsheet
# Note: overall_score_baseline = 0.70
```

### Step 2: Identify Weak Metric
```
Results:
- Faithfulness: 0.75 ✓
- Answer Relevancy: 0.72 ✓
- Context Precision: 0.55 ⚠ LOW
- Context Recall: 0.78 ✓
```

### Step 3: Make Targeted Change
```python
# Low context precision → reduce chunk size
CHUNK_SIZE = 700  # Was 900
```

### Step 4: Re-evaluate
```bash
rm -rf chroma_db_agentic/  # Clear old data
# Re-upload documents
python rag_evaluator.py
# Compare: 0.70 → 0.73 (improved by 0.03)
```

### Step 5: Iterate Until Target Reached
Repeat steps 2-4 until all metrics are >0.7

---

## Troubleshooting Evaluation

### Error: "No indexed documents found"

**Solution**: Upload documents first
```bash
python web_app.py
# Open http://localhost:5000
# Upload PDF files
```

### Error: "Ollama connection failed"

**Solution**: Start Ollama
```bash
ollama serve
# In another terminal
ollama pull llama3.2:latest
```

### Error: "Out of memory"

**Solution**: Reduce data size
```python
# In evaluation_data.json, use fewer questions
# Or clear chroma_db_agentic/ and upload smaller PDF
```

### Evaluation takes >5 minutes

**Normal**: RAGAS evaluation is comprehensive
- Generating answers: 10-20 sec per question
- LLM evaluation: 30-60 sec per question
- Total: ~2-3 minutes for 3 questions is normal

---

## Reports & Results

### evaluation_report.json

```json
{
  "system": "Agentic RAG",
  "scores": {
    "faithfulness": 0.7234,
    "answer_relevancy": 0.7512,
    "context_precision": 0.6856,
    "context_recall": 0.7145
  },
  "overall_score": 0.7187,
  "responses_count": 3,
  "timestamp": "2026-04-19 01:45:30"
}
```

### Tracking Progress

```markdown
| Date | Overall | Faithfulness | Relevancy | Precision | Recall | Changes |
|------|---------|--------------|-----------|-----------|--------|---------|
| 4/19 | 0.70 | 0.72 | 0.71 | 0.66 | 0.71 | Baseline |
| 4/19 | 0.71 | 0.73 | 0.72 | 0.68 | 0.72 | K=20 |
| 4/19 | 0.73 | 0.75 | 0.74 | 0.70 | 0.74 | Size=800 |
```

---

## Best Practices

### ✅ DO

- **Run evaluation regularly**: After parameter changes
- **Document changes**: Track what you modified
- **Use version control**: Commit before/after
- **Test incrementally**: Change one parameter at a time
- **Monitor trends**: Track scores over time
- **Verify manually**: Check if scores match your perception

### ❌ DON'T

- **Over-optimize**: Don't chase one perfect metric
- **Ignore tradeoffs**: Better accuracy = slower responses
- **Trust scores blindly**: Always verify with manual review
- **Use tiny datasets**: Need 5+ questions for reliable metrics
- **Skip baseline**: Always measure before optimization

---

## Next Steps

1. **Upload documents**: Use web_app.py
2. **Create test questions**: Edit evaluation_data.json
3. **Run evaluation**: `python rag_evaluator.py`
4. **Review scores**: Check evaluation_report.json
5. **Optimize**: Adjust parameters and re-evaluate
6. **Monitor**: Track improvements over time

---

## Summary

| Aspect | Details |
|--------|---------|
| **Tool** | RAGAS framework with 4 metrics |
| **Workflow** | Upload docs → Create questions → Run evaluation → Optimize |
| **Target Score** | 0.70+ overall (0.6-0.8 for each metric) |
| **Time** | 2-5 minutes per evaluation run |
| **Output** | Visual report + JSON results |
| **Goal** | Measure and improve answer quality |

**Ready to evaluate your Agentic RAG system!** 🚀

```bash
python rag_evaluator.py
```
