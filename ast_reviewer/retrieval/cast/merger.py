from typing import List
from .chunk import UniversalChunk, ChunkMetrics
from .config import CASTConfig

class ChunkMerger:
    """Handles greedy merging of adjacent chunks."""
    
    def __init__(self, config: CASTConfig):
        self.config = config

    def merge(self, chunks: List[UniversalChunk], content: str) -> List[UniversalChunk]:
        """Greedily merge adjacent chunks."""
        if len(chunks) <= 1:
            return chunks
            
        sorted_chunks = sorted(chunks, key=lambda c: c.start_line)
        result = []
        current_chunk = sorted_chunks[0]
        
        for next_chunk in sorted_chunks[1:]:
            if self._can_merge(current_chunk, next_chunk):
                # Attempt merge
                combined_content = current_chunk.content + "\n" + next_chunk.content
                metrics = ChunkMetrics.from_content(combined_content)
                
                if metrics.non_whitespace_chars <= self.config.max_chunk_size:
                    current_chunk = self._create_merged_chunk(current_chunk, next_chunk, combined_content)
                else:
                    result.append(current_chunk)
                    current_chunk = next_chunk
            else:
                result.append(current_chunk)
                current_chunk = next_chunk
                
        result.append(current_chunk)
        return result

    def _can_merge(self, current: UniversalChunk, next_chunk: UniversalChunk) -> bool:
        # Check compatibility
        compatible = False
        if current.concept == next_chunk.concept:
            compatible = True
        elif {current.concept, next_chunk.concept} <= {"COMMENT", "DEFINITION", "BLOCK"}:
             compatible = True
        
        if not compatible:
            return False

        # Check gap
        gap = next_chunk.start_line - current.end_line
        max_gap = 5
        if "COMMENT" in [current.concept, next_chunk.concept]:
            max_gap = 1
            
        return gap <= max_gap

    def _create_merged_chunk(self, current: UniversalChunk, next_chunk: UniversalChunk, content: str) -> UniversalChunk:
        name = current.name
        if next_chunk.concept == "DEFINITION":
            name = next_chunk.name
        elif current.concept == "DEFINITION":
            name = current.name
            
        concept = current.concept if current.concept == "DEFINITION" else next_chunk.concept
        
        return UniversalChunk(
            concept=concept,
            name=name,
            content=content,
            start_line=current.start_line,
            end_line=next_chunk.end_line,
            metadata=current.metadata
        )
