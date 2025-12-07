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
        # Context Injection (Breadcrumbs):
        # Prepend the name and type to the content so that the embedding model & retrieval
        # see the context even if the chunk is just a logic fragment.
        
        # Detect indentation of the first NON-EMPTY line
        indent = ""
        if self.content:
            for line in self.content.splitlines():
                if line.strip(): # found first non-empty line
                    match = re.match(r"^(\s*)", line)
                    if match:
                        indent = match.group(1)
                    break
        
        context_header = f"{indent}# Context: {self.name} ({self.concept})\n"
        
        # Avoid double header if content already starts with it
        final_content = self.content
        if not final_content.strip().startswith("# Context:"):
            final_content = context_header + final_content

        return {
            "type": self.concept,
            "name": self.name,
            "content": final_content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "metadata": self.metadata
        }
