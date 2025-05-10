document.addEventListener('DOMContentLoaded', () => {
    const userQueryInput = document.getElementById('user-query');
    const submitQueryButton = document.getElementById('submit-query');
    const responseArea = document.getElementById('response-area');

    const backendUrl = 'http://localhost:8000'; // Base URL for API
    const queryEndpoint = `${backendUrl}/query`; // Endpoint for queries

    const addMessageToChat = (message, sender, sources = null) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        
        // Sanitize message content to prevent XSS if it's directly from API
        const messageText = document.createElement('p');
        messageText.textContent = message;
        messageDiv.appendChild(messageText);

        if (sender === 'bot' && sources && sources.length > 0) {
            const sourcesTitle = document.createElement('p');
            sourcesTitle.textContent = 'Sources:';
            sourcesTitle.style.fontWeight = 'bold';
            sourcesTitle.style.marginTop = '10px';
            messageDiv.appendChild(sourcesTitle);

            const sourcesList = document.createElement('ul');
            sourcesList.classList.add('sources-list'); // Added class for styling
            
            sources.forEach(source => {
                const listItem = document.createElement('li');
                let sourceData = source;

                // If source is a string, try to parse it as JSON
                if (typeof source === 'string') {
                    try {
                        sourceData = JSON.parse(source);
                    } catch (e) {
                        console.warn('Could not parse source string:', source, e);
                    }
                }

                // Create element for source metadata (file, chunk ID)
                const metaDiv = document.createElement('div');
                metaDiv.classList.add('source-meta');

                if (sourceData && typeof sourceData === 'object') {
                    const docName = sourceData.document_name || 'Unknown Document';
                    const chunkId = sourceData.chunk_id !== undefined ? sourceData.chunk_id : 'N/A';
                    const displayName = docName.length > 60 ? docName.substring(0, 57) + '...' : docName;
                    metaDiv.textContent = `File: ${displayName} (Chunk ID: ${chunkId})`;
                    listItem.appendChild(metaDiv);
                    
                    // Check for and display snippet if available
                    if (sourceData.snippet) {
                        const chunkPreviewDiv = document.createElement('div');
                        chunkPreviewDiv.classList.add('source-chunk-preview');
                        const previewText = sourceData.snippet.length > 200 
                            ? sourceData.snippet.substring(0, 197) + '...' 
                            : sourceData.snippet;
                        chunkPreviewDiv.textContent = previewText;
                        listItem.appendChild(chunkPreviewDiv);
                    }
                } else {
                    metaDiv.textContent = typeof sourceData === 'string' && sourceData.length > 80 ? sourceData.substring(0, 77) + '...' : sourceData;
                    listItem.appendChild(metaDiv);
                }

                if (!listItem.hasChildNodes()) {
                    // Fallback if no metadata was added to the list item
                    const fallbackText = document.createElement('div');
                    fallbackText.textContent = "Unknown source";
                    listItem.appendChild(fallbackText);
                }

                sourcesList.appendChild(listItem);
            });
            messageDiv.appendChild(sourcesList);
        }

        responseArea.appendChild(messageDiv);
        responseArea.scrollTop = responseArea.scrollHeight; // Scroll to the bottom
    };

    const handleQuerySubmit = async () => {
        const query = userQueryInput.value.trim();
        if (!query) return;

        addMessageToChat(query, 'user');
        userQueryInput.value = ''; // Clear input field

        try {
            // Add a thinking indicator for the bot
            addMessageToChat('Thinking...', 'bot');
            const thinkingMessage = responseArea.lastChild;

            const response = await fetch(queryEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: query }), // Updated request body to match backend
            });

            // Remove the thinking indicator
            if (thinkingMessage && thinkingMessage.textContent === 'Thinking...') {
                 responseArea.removeChild(thinkingMessage);
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail}`);
            }

            const data = await response.json();
            // Updated to use 'answer' and 'sources' from backend response
            const botResponse = data.answer || 'No answer from server.';
            const sources = data.sources || []; 
            addMessageToChat(botResponse, 'bot', sources);

        } catch (error) {
            console.error('Error fetching response:', error);
            addMessageToChat(`Error: ${error.message || 'Could not connect to the server.'}`, 'bot');
        }
    };

    submitQueryButton.addEventListener('click', handleQuerySubmit);
    userQueryInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleQuerySubmit();
        }
    });

    // Initial bot message
    addMessageToChat('Hello! How can I help you today?', 'bot');
}); 