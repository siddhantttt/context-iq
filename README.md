# Context IQ

A simple Retrieval-Augmented Generation (RAG) system for querying your documents using AI.

## Overview

Tiny RAG is a lightweight RAG system that allows you to:

1. Upload documents (PDF, DOCX, TXT)
2. Index their content for semantic search
3. Ask questions about your documents
4. Get AI-generated answers with relevant source citations

The system consists of two main components:

- **Backend**: A FastAPI application that handles document processing, vector indexing, and AI-powered question answering
- **Frontend**: A web interface for chatting with your documents and managing document uploads

## Project Structure

```
tiny-rag/
├── backend/                # Backend API and processing logic
│   ├── app.py              # FastAPI application
│   ├── models.py           # Database models
│   ├── embeddings.py       # Text embedding utilities
│   ├── extract.py          # Document text extraction
│   ├── index.py            # Vector indexing and retrieval
│   └── requirements.txt    # Python dependencies
├── frontend/               # Frontend web interface
│   ├── index.html          # Chat interface
│   ├── documents.html      # Document management interface
│   ├── style.css           # CSS styling
│   ├── script.js           # JavaScript functionality
│   └── README.md           # Frontend setup instructions
└── README.md               # This file
```

## Quick Start

### 1. Set Up the Backend

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The backend will be running at http://localhost:8000.

### 2. Set Up the Frontend

The frontend is a static web application that can be served in various ways:

**Option 1**: Open `frontend/index.html` directly in your browser

**Option 2**: Use Python's built-in HTTP server
```bash
# From the project root directory
python -m http.server
# Then visit http://localhost:8000/frontend/
```

**Option 3**: Use VS Code's Live Server extension or any other static file server

For detailed frontend setup instructions, see [frontend/README.md](frontend/README.md).

## Using the Application

### Document Management

1. Navigate to the "Manage Documents" tab
2. Upload documents using the file upload form
3. View your uploaded documents 
4. Click "View Details" to see document chunks

### Chat Interface

1. Navigate to the "Chat" tab
2. Type your question in the input field
3. Press "Send" or hit Enter
4. The system will retrieve relevant information from your documents and provide an answer
5. Sources used for generating the answer will be displayed below the response

## API Endpoints

The backend provides the following API endpoints:

- `POST /documents` - Upload a document
- `GET /documents` - List all documents
- `GET /documents/{doc_id}` - Get details of a specific document
- `POST /query` - Ask a question about your documents

## Technologies Used

- **Backend**:
  - FastAPI (Python web framework)
  - FAISS (Vector search library)
  - SQLModel (Database ORM)
  - OpenAI API (For embeddings and text generation)
  - Various document processing libraries (PyPDF, docx2txt)

- **Frontend**:
  - HTML/CSS/JavaScript
  - Fetch API for backend communication

## License

[Add your license information here]

## Acknowledgements

[Add any acknowledgements or credits here] 
