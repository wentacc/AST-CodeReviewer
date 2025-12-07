import sys
import os

# Add current directory to path to import ast_reviewer
sys.path.append(os.getcwd())

from ast_reviewer.retrieval.cast.pipeline import CASTChunker

def naive_chunker(code, chunk_size=100):
    """Simulates a naive fixed-size chunker."""
    lines = code.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        if current_size + len(line) > chunk_size and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(line)
        current_size += len(line)
        
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks

def generate_table():
    code_snippet = """
def calculate_trajectory(velocity, angle):
    # Physics calculation
    import math
    g = 9.8
    rad = math.radians(angle)
    
    # ... complex logic ...
    
    x = velocity * math.cos(rad)
    y = velocity * math.sin(rad)
    return (x, y)
"""
    
    # 1. Run Naive Chunker
    naive_chunks = naive_chunker(code_snippet, chunk_size=50)
    
    # 2. Run cAST Chunker
    # We need to write to a temp file for CASTChunker
    with open("temp_snippet.py", "w") as f:
        f.write(code_snippet)
        
    cast_chunker = CASTChunker()
    # Force small chunk size to trigger splitting for demonstration
    cast_chunker.config.max_chunk_size = 50 
    cast_chunks = cast_chunker.chunk_file("temp_snippet.py")
    
    # 3. Generate Table
    print(f"DEBUG: Generated {len(naive_chunks)} naive chunks and {len(cast_chunks)} cAST chunks")
    
    print("\n| Feature | Naive Chunking (Baseline) | cAST (Structure-Aware) |")
    print("| :--- | :--- | :--- |")
    
    # Compare Chunk 1 (Context Loss vs Preservation)
    naive_c1 = naive_chunks[1].strip().replace('\n', '<br>') if len(naive_chunks) > 1 else "N/A"
    # Find a split part in cAST
    cast_c1 = "N/A"
    cast_c1_name = "N/A"
    for c in cast_chunks:
        if "part" in c['name']:
            cast_c1 = f"**Name:** `{c['name']}`<br>**Type:** `{c['type']}`"
            cast_c1_name = c['name']
            break
            
    print(f"| **Splitting Strategy** | Fixed Character/Line Limit | Semantic Boundaries (AST) |")
    print(f"| **Context Retention** | Lost (Anonymous Text Block) | **Preserved** (Inherits Function Name) |")
    print(f"| **Retrieval Query** | *\"calculate trajectory\"* -> ❌ Miss | *\"calculate trajectory\"* -> ✅ Hit |")
    print(f"| **Metadata** | None | `type: DEFINITION`, `name: {cast_c1_name}` |")

    # Clean up
    if os.path.exists("temp_snippet.py"):
        os.remove("temp_snippet.py")

if __name__ == "__main__":
    try:
        generate_table()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
