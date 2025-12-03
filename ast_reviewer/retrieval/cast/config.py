from dataclasses import dataclass

@dataclass
class CASTConfig:
    """Configuration for cAST algorithm."""
    max_chunk_size: int = 1200  # non-whitespace chars
    min_chunk_size: int = 50
    merge_threshold: float = 0.8
    safe_token_limit: int = 6000
