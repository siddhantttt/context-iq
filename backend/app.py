import os
import tempfile
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from models import Document, Chunk, create_db_and_tables, get_session
from index import add_document, answer, save_index

# Initialize FastAPI
app = FastAPI(title="Quick-RAG API", 
              description="A minimal RAG (Retrieval-Augmented Generation) API",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and response models
class QueryRequest(BaseModel):
    question: str
    doc_ids: Optional[List[int]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]

class DocumentResponse(BaseModel):
    id: int
    name: str

class DocumentDetailResponse(BaseModel):
    id: int
    name: str
    mime_type: str
    chunks: List[dict]

# Create tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Save index on shutdown
@app.on_event("shutdown")
def on_shutdown():
    save_index()

# Endpoints
@app.post("/documents", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, or TXT) for processing.
    """
    # Create a temporary file to store the upload
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        # Write uploaded file content to temp file
        content = await file.read()
        temp.write(content)
        temp_path = temp.name
    
    try:
        # Process the document
        doc_id = await add_document(temp_path, file.filename)
        
        # Return document ID
        return {"id": doc_id, "name": file.filename}
    finally:
        # Clean up the temp file
        os.unlink(temp_path)

@app.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: int, session: Session = Depends(get_session)):
    """
    Get document details including its chunks.
    """
    # Get document
    document = session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get chunks
    chunks_query = select(Chunk).where(Chunk.doc_id == doc_id)
    chunks = session.exec(chunks_query).all()
    
    # Format response
    chunks_data = [{"id": chunk.id, "text": chunk.text} for chunk in chunks]
    
    return {
        "id": document.id,
        "name": document.name,
        "mime_type": document.mime_type,
        "chunks": chunks_data
    }

@app.get("/documents")
async def list_documents(session: Session = Depends(get_session)):
    """
    List all documents.
    """
    documents = session.exec(select(Document)).all()
    return [{"id": doc.id, "name": doc.name} for doc in documents]

@app.post("/query", response_model=QueryResponse)
async def query_documents(query: QueryRequest):
    """
    Query documents and get an AI-generated answer.
    """
    result = await answer(query.question, query.doc_ids)
    return result

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 