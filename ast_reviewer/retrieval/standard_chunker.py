import os

class StandardChunker:
    """
    A baseline chunker that splits text into fixed-size chunks with overlap.
    Does not respect code structure (AST).
    """
    def __init__(self, chunk_size=600, overlap=100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        chunks = []
        start = 0
        content_len = len(content)
        
        chunk_id = 0
        while start < content_len:
            end = min(start + self.chunk_size, content_len)
            chunk_text = content[start:end]
            
            # Create chunk dict compatible with VectorStore
            chunks.append({
                "name": f"{os.path.basename(file_path)}_std",
                "start_line": chunk_id, # Using chunk_id as proxy for line since we are char based
                "end_line": chunk_id + 1,
                "content": chunk_text,
                "type": "text_chunk"
            })
            
            chunk_id += 1
            start += (self.chunk_size - self.overlap)
            
        return chunks
