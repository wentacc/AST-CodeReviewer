import re
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ChunkMetrics:
    """Metrics for measuring chunk quality and size."""
    non_whitespace_chars: int
    total_chars: int
    lines: int

    @classmethod
    def from_content(cls, content: str) -> "ChunkMetrics":
        non_ws = len(re.sub(r"\s", "", content))
        total = len(content)
        lines = len(content.split("\n"))
        return cls(non_ws, total, lines)

@dataclass
class UniversalChunk:
    """Universal Chunk model for cAST."""
    concept: str  # DEFINITION, BLOCK, COMMENT, STRUCTURE
    name: str
    content: str
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "type": self.concept,
            "name": self.name,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "metadata": self.metadata
        }
