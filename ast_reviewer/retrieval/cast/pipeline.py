from typing import List, Dict
from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from .config import CASTConfig
from .extractor import ConceptExtractor
from .splitter import ChunkSplitter
from .merger import ChunkMerger

class CASTChunker:
    """Main entry point for cAST chunking."""
    
    def __init__(self):
        self.PY_LANGUAGE = Language(tspython.language())
        self.parser = Parser(self.PY_LANGUAGE)
        self.config = CASTConfig()
        
        self.extractor = ConceptExtractor()
        self.splitter = ChunkSplitter(self.config)
        self.merger = ChunkMerger(self.config)

    def parse(self, code):
        return self.parser.parse(bytes(code, "utf8"))

    def chunk_file(self, file_path: str) -> List[Dict]:
        with open(file_path, "r") as f:
            code = f.read()
        
        tree = self.parse(code)
        
        # 1. Extract
        universal_chunks = self.extractor.extract(tree.root_node, code)
        
        # 2. Split
        split_chunks = []
        for chunk in universal_chunks:
            split_chunks.extend(self.splitter.validate_and_split(chunk, code))
            
        # 3. Merge
        optimized_chunks = self.merger.merge(split_chunks, code)
        
        return [c.to_dict() for c in optimized_chunks]

if __name__ == "__main__":
    import os
    chunker = CASTChunker()
    print("Testing Modular cAST Chunker on sample_code.py...")
    if os.path.exists("sample_code.py"):
        chunks = chunker.chunk_file("sample_code.py")
        print(f"Found {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1}: [{chunk['type']}] {chunk['name']} (Lines {chunk['start_line']}-{chunk['end_line']})")
            print(f"  Content Preview: {chunk['content'][:50]}...")
            print("-" * 20)
    else:
        print("sample_code.py not found.")
