import os
from typing import List
import openai
import tiktoken
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Get API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536  # Dimensions for text-embedding-3-small

# Get encoder for calculating token lengths
encoder = tiktoken.get_encoding("cl100k_base")  # The encoding used by text-embedding-3 models

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    return len(encoder.encode(text))

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
async def embed(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI's API.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each is a list of floats)
    """
    if not texts:
        return []
    
    client = openai.AsyncOpenAI(api_key=openai.api_key)
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    
    # Extract embeddings from the response
    embeddings = [item.embedding for item in response.data]
    return embeddings

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """
    Split text into chunks of approximately chunk_size tokens.
    Simple implementation that splits on periods and then combines sentences.
    
    Args:
        text: The text to split into chunks
        chunk_size: Target size of each chunk in tokens
        
    Returns:
        List of text chunks
    """
    # Get chunk size from environment or use default
    chunk_size_tokens = int(os.getenv("CHUNK_SIZE_TOKENS", chunk_size))
    
    # Split on sentences (simple approach)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        # Add a period back to the sentence
        if not sentence.endswith('.'):
            sentence = sentence + '.'
            
        sentence_size = count_tokens(sentence)
        
        # If adding this sentence would exceed the chunk size,
        # save the current chunk and start a new one
        if current_size + sentence_size > chunk_size_tokens and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks 