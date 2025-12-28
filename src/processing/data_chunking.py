"""
Document chunking module for processing repository markdown files.

This module provides sliding window chunking with overlap to maintain
context across chunk boundaries - essential for good search results.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class Chunk:
    """Represents a single chunk of document content with metadata."""
    content: str
    start_char: int
    end_char: int
    chunk_index: int
    filename: str
    title: str | None = None
    # Additional frontmatter fields stored here
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for serialization."""
        result = asdict(self)
        # Flatten metadata into the result
        if self.metadata:
            result.update(self.metadata)
            del result['metadata']
        return result


def sliding_window_chunk(
    text: str,
    chunk_size: int = 1500,
    overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks using a sliding window.
    
    Args:
        text: The text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of chunk dictionaries with content and position info
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")
    
    if not text or not text.strip():
        return []
    
    chunks = []
    start = 0
    chunk_index = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # Try to break at a natural boundary (paragraph, sentence, word)
        if end < text_length:
            # Look for paragraph break first
            break_point = text.rfind('\n\n', start, end)
            if break_point == -1 or break_point <= start:
                # Look for single newline
                break_point = text.rfind('\n', start, end)
            if break_point == -1 or break_point <= start:
                # Look for sentence end
                for punct in ['. ', '? ', '! ']:
                    bp = text.rfind(punct, start, end)
                    if bp > start:
                        break_point = bp + 1
                        break
            if break_point > start:
                end = break_point
        
        chunk_content = text[start:end].strip()
        
        if chunk_content:  # Only add non-empty chunks
            chunks.append({
                'content': chunk_content,
                'start_char': start,
                'end_char': end,
                'chunk_index': chunk_index
            })
            chunk_index += 1
        
        # Move start position (with overlap)
        start = end - overlap if end < text_length else text_length
    
    return chunks


def process_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = 1500,
    overlap: int = 200
) -> List[Chunk]:
    """
    Process a list of documents from read_repo_data into chunks.
    
    Args:
        documents: List of document dicts from read_repo_data()
                   Each has 'content', 'filename', and optional frontmatter fields
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of Chunk objects with content and full metadata
    """
    all_chunks = []
    
    for doc in documents:
        # Extract content (required field)
        content = doc.get('content', '')
        if not content:
            continue
        
        # Extract known fields
        filename = doc.get('filename', 'unknown')
        title = doc.get('title')
        
        # Collect remaining frontmatter as metadata
        metadata = {
            k: v for k, v in doc.items() 
            if k not in ('content', 'filename', 'title')
        }
        
        # Generate chunks for this document
        raw_chunks = sliding_window_chunk(content, chunk_size, overlap)
        
        for raw_chunk in raw_chunks:
            chunk = Chunk(
                content=raw_chunk['content'],
                start_char=raw_chunk['start_char'],
                end_char=raw_chunk['end_char'],
                chunk_index=raw_chunk['chunk_index'],
                filename=filename,
                title=title,
                metadata=metadata if metadata else None
            )
            all_chunks.append(chunk)
    
    return all_chunks


def chunks_to_dicts(chunks: List[Chunk]) -> List[Dict[str, Any]]:
    """Convert list of Chunk objects to list of dictionaries."""
    return [chunk.to_dict() for chunk in chunks]