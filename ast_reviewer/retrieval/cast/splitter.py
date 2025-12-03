from typing import List
from .chunk import UniversalChunk, ChunkMetrics
from .config import CASTConfig

class ChunkSplitter:
    """Handles recursive splitting of large chunks."""
    
    def __init__(self, config: CASTConfig):
        self.config = config

    def validate_and_split(self, chunk: UniversalChunk, content: str) -> List[UniversalChunk]:
        """Validate chunk size and split if necessary."""
        metrics = ChunkMetrics.from_content(chunk.content)
        
        if metrics.non_whitespace_chars <= self.config.max_chunk_size:
            return [chunk]
            
        # Too large, apply recursive splitting
        return self._recursive_split(chunk, content)

    def _recursive_split(self, chunk: UniversalChunk, content: str) -> List[UniversalChunk]:
        """Split chunk based on content analysis."""
        lines = chunk.content.split("\n")
        
        # Simple line-based splitting
        if len(lines) <= 2:
             # Placeholder for emergency char split
             return [chunk] 
             
        mid = len(lines) // 2
        part1_content = "\n".join(lines[:mid])
        part2_content = "\n".join(lines[mid:])
        
        chunk1 = UniversalChunk(
            concept=chunk.concept,
            name=f"{chunk.name}_part1",
            content=part1_content,
            start_line=chunk.start_line,
            end_line=chunk.start_line + mid - 1,
            metadata=chunk.metadata
        )
        chunk2 = UniversalChunk(
            concept=chunk.concept,
            name=f"{chunk.name}_part2",
            content=part2_content,
            start_line=chunk.start_line + mid,
            end_line=chunk.end_line,
            metadata=chunk.metadata
        )
        
        result = []
        for c in [chunk1, chunk2]:
            result.extend(self.validate_and_split(c, content))
            
        return result
