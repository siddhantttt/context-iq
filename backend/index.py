import os
import faiss
import numpy as np
import json
import tempfile
from typing import List, Dict, Any, Tuple, Optional
import openai
from sqlmodel import Session, select

from models import Document, Chunk, engine
# Import with an alias to avoid potential name conflicts
from embeddings import embed, chunk_text as split_text
from extract import extract_text, detect_mimetype

# Vector dimensions for the embedding model
EMBEDDING_DIMENSIONS = 1536  # Dimensions for text-embedding-3-small
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", ".faiss")
TOP_K = 4  # Number of chunks to retrieve in search

# Initialize FAISS index
index = faiss.IndexFlatL2(EMBEDDING_DIMENSIONS)
# Store mapping of FAISS ids to DB chunk ids
id_map = {}

async def add_document(temp_file_path: str, original_file_name: str) -> int:
    """
    Process a document: extract text, chunk it, generate embeddings, 
    store in FAISS and database.
    
    Args:
        temp_file_path: Path to the temporary uploaded file content.
        original_file_name: The original name of the file (e.g., "G05 Abstract.pdf").
        
    Returns:
        Document ID
    """
    # Extract text from file using temp_file_path for content and original_file_name for type detection
    extracted_text = extract_text(temp_file_path, original_filename=original_file_name)
    
    # Determine mime_type using the original_file_name for storing in DB
    db_mime_type = detect_mimetype(original_file_name) 
    
    # Create document in database
    with Session(engine) as session:
        document = Document(name=original_file_name, mime_type=db_mime_type)
        session.add(document)
        session.commit()
        session.refresh(document)
        doc_id = document.id
    
    # Chunk the text
    # If extraction failed, extracted_text might be an error/warning string
    if extracted_text.startswith("[Error") or extracted_text.startswith("[Warning"):
        # Optionally, log this information or handle it
        # For now, we proceed, but no chunks will be created if it's just a warning/error string
        chunks = [] 
    else:
        chunks = split_text(extracted_text)
    
    if not chunks:
        # If no chunks (e.g., empty doc or extraction failed to produce usable text),
        # still return doc_id as the document entry is created.
        return doc_id
    
    # Generate embeddings for all chunks
    embeddings = await embed(chunks)
    
    # Store chunks and embeddings
    with Session(engine) as session:
        for i, (chunk_text_content, embedding_vector) in enumerate(zip(chunks, embeddings)):
            chunk = Chunk(doc_id=doc_id, text=chunk_text_content)
            session.add(chunk)
            session.commit()
            session.refresh(chunk)
            
            vector = np.array([embedding_vector], dtype=np.float32)
            faiss_id = index.ntotal
            index.add(vector)
            id_map[faiss_id] = chunk.id
            
    save_index()
    return doc_id

def load_index():
    """Load FAISS index from disk if it exists."""
    global index, id_map
    
    index_file = f"{FAISS_INDEX_PATH}.index"
    map_file = f"{FAISS_INDEX_PATH}.map"

    if os.path.exists(index_file) and os.path.exists(map_file):
        try:
            index = faiss.read_index(index_file)
            with open(map_file, "r") as f:
                # Ensure keys are integers after loading from JSON
                id_map_str_keys = json.load(f)
                id_map = {int(k): v for k, v in id_map_str_keys.items()}
            print(f"Successfully loaded FAISS index from {index_file} and map from {map_file}. Index size: {index.ntotal}")
        except Exception as e:
            print(f"Error loading index: {e}. Initializing new index.")
            index = faiss.IndexFlatL2(EMBEDDING_DIMENSIONS)
            id_map = {}
    else:
        print("FAISS index files not found. Initializing new index.")
        index = faiss.IndexFlatL2(EMBEDDING_DIMENSIONS)
        id_map = {}

def save_index():
    """Save FAISS index to disk."""
    dir_path = os.path.dirname(FAISS_INDEX_PATH)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    
    index_file = f"{FAISS_INDEX_PATH}.index"
    map_file = f"{FAISS_INDEX_PATH}.map"

    try:
        faiss.write_index(index, index_file)
        with open(map_file, "w") as f:
            json.dump(id_map, f)
        print(f"Successfully saved FAISS index to {index_file} and map to {map_file}.")
    except Exception as e:
        print(f"Error saving FAISS index: {e}")

async def search(query: str, doc_ids: Optional[List[int]] = None, k: int = TOP_K) -> List[Dict[str, Any]]:
    """
    Search for relevant chunks based on a query.
    
    Args:
        query: Search query
        doc_ids: Optional list of document IDs to restrict search to
        k: Number of results to return (ensure k <= index.ntotal if index is not empty)
        
    Returns:
        List of dictionaries with chunk information
    """
    if index.ntotal == 0:
        print("Search called but FAISS index is empty.")
        return []

    query_embedding = await embed([query])
    if not query_embedding:
        return []
    
    query_vector = np.array(query_embedding[0], dtype=np.float32).reshape(1, -1)
    
    # Ensure k is not greater than the number of items in the index
    actual_k = min(k, index.ntotal)
    if actual_k == 0 : # Should be caught by index.ntotal == 0, but defensive check
        return []

    distances, indices = index.search(query_vector, actual_k)
    
    results = []
    with Session(engine) as session:
        for i, faiss_id_int in enumerate(indices[0]): # faiss_id is an int
            # FAISS can return -1 if fewer than k results are found or if vectors are identical.
            if faiss_id_int < 0:
                continue
            
            # id_map keys are integers
            if faiss_id_int in id_map:
                chunk_id = id_map[faiss_id_int]
                chunk = session.get(Chunk, chunk_id)
                if not chunk:
                    continue
                
                if doc_ids and chunk.doc_id not in doc_ids:
                    continue
                    
                document = session.get(Document, chunk.doc_id)
                if not document:
                    continue
                    
                results.append({
                    "chunk_id": chunk_id,
                    "document_id": chunk.doc_id,
                    "document_name": document.name,
                    "text": chunk.text,
                    "score": float(distances[0][i]) # Ensure score is float for JSON serialization
                })
            else:
                print(f"Warning: FAISS ID {faiss_id_int} not found in id_map.")

    results.sort(key=lambda x: x["score"]) # Lower distance is better
    return results # Already sliced to actual_k by FAISS search

async def answer(question: str, doc_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Generate an answer for a question using RAG.
    
    Args:
        question: The question to answer
        doc_ids: Optional list of document IDs to restrict search to
        
    Returns:
        Dictionary with answer and sources
    """
    relevant_chunks = await search(question, doc_ids)
    
    if not relevant_chunks:
        return {
            "answer": "I couldn't find any relevant information to answer your question based on the current documents and query.",
            "sources": []
        }
    
    context = "\n\n---\n\n".join([chunk["text"] for chunk in relevant_chunks])
    
    prompt = f"""You are a helpful assistant that provides accurate information based on the given context.
If the information to answer the question is not in the context, say 'I don't have enough information to answer this question.'

Context:
---
{context}
---

Question: {question}

Answer:"""

    try:
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        answer_text = response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI for completion: {e}")
        answer_text = "[Error: Could not generate an answer due to an LLM API issue.]"
    
    sources = [{
        "chunk_id": chunk["chunk_id"],
        "document_id": chunk["document_id"], 
        "document_name": chunk["document_name"],
        "snippet": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
    } for chunk in relevant_chunks]
    
    return {
        "answer": answer_text,
        "sources": sources
    }

# Initialize by loading the index on startup
load_index() 