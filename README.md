# Quick-RAG

A minimal Retrieval-Augmented Generation (RAG) API built with FastAPI, OpenAI, and FAISS, structured as a monorepo.

## Project Structure

```
quick-rag/
├── backend/            # FastAPI application and RAG logic
│   ├── app.py
│   ├── embeddings.py
│   ├── extract.py
│   ├── index.py
│   ├── models.py
│   └── requirements.txt
├── frontend/           # Placeholder for a future frontend application
├── .gitignore
├── README.md
├── quick_rag.db        # SQLite database (generated at root)
└── .faiss.*            # FAISS index files (generated at root)
```

## Features

- Upload documents (PDF, DOCX, TXT)
- Automatic text extraction and chunking
- Vector search using FAISS
- Question answering using OpenAI's GPT models
- REST API with FastAPI

## Setup

1. **Navigate to the backend directory and create a virtual environment**

   From the project root:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   cd .. # Go back to project root for next steps if needed, or stay in backend/
   ```

2. **Install dependencies**

   Ensure your virtual environment is activated. From the project root:
   ```bash
   pip install -r backend/requirements.txt
   ```
   Or if you are inside the `backend` directory:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**

   These should be set in the environment from which you run the backend server (e.g., your shell in the project root).
   ```bash
   export OPENAI_API_KEY=your_openai_api_key
   # Optional:
   # export OPENAI_MODEL=gpt-4o-mini  # or gpt-3.5-turbo
   # export CHUNK_SIZE_TOKENS=500
   # export FAISS_INDEX_PATH=.faiss # Default, creates .faiss.index and .faiss.map at root
   ```

## Running the API

   From the project root, with the virtual environment (created in `backend/.venv`) activated:
   ```bash
   uvicorn backend.app:app --reload
   ```

   The API will be available at `http://localhost:8000`.

   API documentation is available at `http://localhost:8000/docs`.

## API Endpoints

- `POST /documents` - Upload a document
- `GET /documents` - List all documents
- `GET /documents/{doc_id}` - Get document details and chunks
- `POST /query` - Ask a question about the documents

## Example Usage

   (Ensure the server is running as described above)

### Upload a document

   ```bash
   curl -X POST "http://localhost:8000/documents" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/document.pdf"
   ```

### Query documents

   ```bash
   curl -X POST "http://localhost:8000/query" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What is the main topic of the document?",
       "doc_ids": [1, 2]  # Optional, limit to specific documents
     }'
   ```

## Architecture

- **FastAPI**: Web framework for the REST API
- **OpenAI API**: For embeddings and LLM inference
- **FAISS**: Vector database for similarity search
- **SQLite + SQLModel**: Document and chunk metadata storage (database file at project root)

## System Flow

1. **Document Processing**: 
   - Extract text from uploaded documents
   - Split text into chunks of ~500 tokens
   - Generate embeddings for each chunk
   - Store in FAISS (index files at project root) and SQLite (DB file at project root)

2. **Query Processing**:
   - Embed the query
   - Find top-k relevant chunks
   - Compose prompt with context and question
   - Generate answer with LLM
   - Return answer and sources 