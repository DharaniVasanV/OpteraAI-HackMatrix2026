"""
app/services/retrieval_service.py

Core Knowledge Retrieval Service:
- STEPS 3-6: Embedding + Cosine Similarity search via local model (zero-cost)
- STEP 8-9: Groq used ONLY to format the top retrieved chunk into a clean answer
  (minimal tokens: context trimmed to 1000 chars, answer capped at 400 tokens)
"""

import json
import time
import re
import sys
sys.path.insert(0, r"E:\AgentOS")
from groq_rotation import groq_chat_sync

from app.config.settings import get_settings
from app.services.embedder import generate_query_embedding
from app.db.vector_search import search_vector_database
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are a precise Knowledge Assistant. Answer the question using ONLY the provided context.
Be concise and direct. If the answer is not in the context, say: 'I could not find that information in the knowledge base.'"""


async def process_retrieval_query(user_query: str) -> dict:
    start_time = time.time()

    # STEP 2: Validate Query
    if not user_query or not user_query.strip():
        return {
            "status": "failed",
            "reason": "Empty query."
        }

    # STEP 3: Generate Query Embedding (No LLM)
    try:
        logger.info("STEP 3: Generating query embedding...")
        query_vec = generate_query_embedding(user_query)
    except Exception as e:
        logger.error("Query embedding failed: %s", e)
        return {
            "status": "failed",
            "reason": "Query embedding generation failed."
        }

    # STEP 4 & 5: Search Vector Database & Retrieve Top 5 Results
    try:
        logger.info("STEP 4 & 5: Searching vector DB with Cosine Similarity...")
        retrieved_chunks = search_vector_database(user_query, query_vec, top_k=settings.TOP_K)
    except Exception as e:
        logger.error("Vector DB search failed: %s", e)
        return {
            "status": "failed",
            "reason": "Vector database unavailable."
        }

    # STEP 6: Filter & Sort Results
    filtered_chunks = [c for c in retrieved_chunks if c["similarity_score"] >= settings.SIMILARITY_THRESHOLD]
    
    if not filtered_chunks and retrieved_chunks:
        # Include top result if available to ensure best-effort context
        filtered_chunks = retrieved_chunks[:3]

    # Handle NOTHING FOUND case
    if not filtered_chunks:
        processing_time_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "success",
            "query": user_query,
            "answer": "I could not find sufficient information inside the AgentOS Knowledge Base.",
            "retrieved_documents": [],
            "citations": [],
            "confidence": "Low",
            "processing_time_ms": processing_time_ms
        }

    # STEP 7: Build Retrieval Context — only top 2 chunks, trimmed to 800 chars each
    top_chunks = filtered_chunks[:2]
    context_blocks = []
    for idx, chunk in enumerate(top_chunks):
        trimmed = chunk['original_text'][:800]
        block = f"[SOURCE {idx+1}]\n{trimmed}"
        context_blocks.append(block)
    context_str = "\n\n".join(context_blocks)

    # STEP 8-9: Use Groq ONLY to format the answer — minimal token usage
    try:
        logger.info("STEP 8 & 9: Formatting answer via Groq (minimal tokens)...")
        user_prompt = f"Question: {user_query}\n\nContext:\n{context_str}\n\nAnswer:"
        answer = groq_chat_sync(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=400,
        )
        if not answer:
            answer = top_chunks[0]['original_text'][:500] if top_chunks else "I could not find sufficient information inside the AgentOS Knowledge Base."
    except Exception as e:
        logger.warning("Groq formatting failed, returning raw chunk text: %s", e)
        # Graceful fallback: return the best matching chunk text directly
        answer = top_chunks[0]['original_text'][:600] if top_chunks else "I could not find sufficient information inside the AgentOS Knowledge Base."

    # STEP 10: Generate Citations & Document Metadata
    retrieved_documents = []
    citations = []
    max_sim = 0.0

    for c in filtered_chunks:
        sim = c["similarity_score"]
        if sim > max_sim:
            max_sim = sim

        retrieved_documents.append({
            "document_id": c["document_id"],
            "document_name": c["document_name"],
            "chunk_id": c["chunk_id"],
            "similarity_score": sim
        })

        citations.append({
            "document": c["document_name"],
            "chunk": c["chunk_id"],
            "source": "Knowledge Base"
        })

    # STEP 11: Estimate Confidence
    if max_sim >= 0.90:
        confidence = "High"
    elif max_sim >= 0.80:
        confidence = "Medium"
    else:
        confidence = "Low"

    processing_time_ms = int((time.time() - start_time) * 1000)

    # STEP 12: Return JSON
    logger.info("🟢 SUCCESS: RAG Retrieval query processed in %d ms (Confidence: %s)", processing_time_ms, confidence)
    return {
        "status": "success",
        "query": user_query,
        "answer": answer,
        "retrieved_documents": retrieved_documents,
        "citations": citations,
        "confidence": confidence,
        "processing_time_ms": processing_time_ms
    }
