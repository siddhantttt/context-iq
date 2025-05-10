# Tiny RAG Frontend

This is a simple frontend for the Tiny RAG (Retrieval-Augmented Generation) application. It provides a chat interface where users can query documents that have been uploaded to the system.

## Setup Instructions

### 1. Prerequisites

Before setting up the frontend, make sure you have:

- The backend server running (see Backend Setup below)
- A modern web browser (Chrome, Firefox, Safari, Edge)
- Optional: A simple HTTP server if you want to serve the frontend files (Python's http.server, VS Code's Live Server, etc.)

### 2. Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```
   python app.py
   ```

   The backend should now be running at http://localhost:8000.

### 3. Frontend Setup

You can serve the frontend in several ways:

#### Option 1: Open the HTML file directly

Simply open the `frontend/index.html` file in your web browser. This works for basic testing but may have limitations with CORS policies.

#### Option 2: Use Python's built-in HTTP server

1. Navigate to the project root directory
2. Run the following command:
   ```
   python -m http.server
   ```
3. Open your browser and navigate to http://localhost:8000/frontend/

#### Option 3: Use VS Code Live Server extension

If you're using Visual Studio Code:
1. Install the "Live Server" extension
2. Right-click on the `frontend/index.html` file
3. Select "Open with Live Server"

## Using the Application

### 1. Document Management

Currently, the frontend only includes the chat interface for querying documents. Documents must be uploaded using the backend API directly:

```
curl -X POST "http://localhost:8000/documents" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@path/to/your/document.pdf"
```

### 2. Querying Documents

Once documents are uploaded:

1. Open the frontend in your browser
2. Type your question in the input field
3. Press "Send" or hit Enter
4. The system will retrieve relevant information from your documents and provide an answer
5. Sources used for generating the answer will be displayed below the response

## Troubleshooting

### Common Issues

1. **"Error: Could not connect to the server"**
   - Make sure the backend server is running
   - Check that the backend URL in `script.js` matches your backend server address (default: `http://localhost:8000/query`)

2. **CORS Issues**
   - If using the "Open HTML file directly" method, you might encounter CORS errors
   - Use one of the other serving methods or ensure the backend has CORS properly configured

3. **No Documents Available**
   - If you're getting generic responses, you may not have uploaded any documents
   - Use the curl command above or another API client to upload documents

## Extending the Frontend

To add document management features to the frontend:

1. Create a new page or section for document uploads
2. Implement a form that sends files to the `/documents` endpoint
3. Add a document browser that lists documents from the `/documents` GET endpoint
4. Add document detail views using the `/documents/{doc_id}` endpoint

## Technologies Used

- HTML5
- CSS3
- JavaScript (ES6+)
- Fetch API for backend communication 