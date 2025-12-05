from ast_reviewer.retrieval.vector_store import VectorStore
from ast_reviewer.retrieval.cast.pipeline import CASTChunker
import shutil
import os

# Clean up previous db if exists
if os.path.exists("./chroma_db"):
    shutil.rmtree("./chroma_db")

# 1. Chunk
chunker = CASTChunker()
chunks = chunker.chunk_file("complex_test.py")
print(f"Generated {len(chunks)} chunks.")

# 2. Store
vs = VectorStore()
vs.add_chunks(chunks)
print("Added chunks to VectorStore.")

# 3. Query
query = "process data"
results = vs.query(query)
print(f"\nQuery: '{query}'")
for res in results:
    print(f"Match: {res['metadata']['name']} (Dist: {res['distance']})")
    print(f"Snippet: {res['content'][:50]}...")
