import os
import shutil
from ast_reviewer.agents.experts import BugExpert, SecurityExpert, StyleExpert
from ast_reviewer.retrieval.cast.pipeline import CASTChunker
from ast_reviewer.retrieval.standard_chunker import StandardChunker
from ast_reviewer.retrieval.vector_store import VectorStore

# Configuration
OUTPUT_FILE = "experiment_2_report.md"
SAMPLES_TO_TEST = ["generated_projects/sample_10.py", "generated_projects/sample_4.py"]
SNIPPET_SIZE = 30

def get_snippet(code, num_lines=SNIPPET_SIZE):
    lines = code.splitlines()
    if len(lines) <= num_lines:
        return code
    start = len(lines) // 3
    end = start + num_lines
    return "\n".join(lines[start:end])

def run_experiment():
    print("Initializing Experiment 2...")
    
    # Agents
    bug_expert = BugExpert()
    experts = [bug_expert] # Focus on BugExpert for logic issues
    
    # Chunkers
    cast_chunker = CASTChunker()
    std_chunker = StandardChunker(chunk_size=600, overlap=50)
    
    vector_store = VectorStore()
    
    report = "# Experiment 2: Impact of Structure-Aware Retrieval (Ablation Study)\n\n"
    report += "Comparing **Standard Fixed-Size Chunking** vs **cAST (Structure-Aware) Chunking**.\n"
    report += "Focusing on context quality and agent hallucination reduction.\n\n"
    
    for file_path in SAMPLES_TO_TEST:
        filename = os.path.basename(file_path)
        print(f"Processing {filename}...")
        
        with open(file_path, "r") as f:
            full_code = f.read()
            
        snippet = get_snippet(full_code)
        report += f"## Sample: {filename}\n\n"
        report += "### Snippet Reviewed\n"
        report += f"```python\n{snippet}\n```\n\n"
        
        # --- Run Standard Chunker ---
        print("  Running Standard Chunker...")
        vector_store.clear()
        chunks = std_chunker.chunk_file(file_path)
        vector_store.add_chunks(chunks)
        
        query = snippet
        retrieved_std = vector_store.query(query, n_results=3)
        
        report += "### Method A: Standard Retrieval\n"
        report += "**Retrieved Context Snippets:**\n"
        for i, chunk in enumerate(retrieved_std):
            report += f"**Chunk {i+1}:**\n```python\n{chunk}\n```\n"
            
        report += "\n**Agent Review (Standard):**\n"
        comments_std = bug_expert.review(snippet, retrieved_std)
        if not comments_std:
            report += "- No issues found.\n"
        else:
            for c in comments_std:
                report += f"{c}\n"
                
        # --- Run cAST Chunker ---
        print("  Running cAST Chunker...")
        vector_store.clear()
        try:
            chunks = cast_chunker.chunk_file(file_path)
            vector_store.add_chunks(chunks)
        except Exception as e:
            print(f"Error cAST chunking: {e}")
            
        retrieved_cast = vector_store.query(query, n_results=3)
        
        report += "\n### Method B: cAST Retrieval\n"
        report += "**Retrieved Context Snippets:**\n"
        for i, chunk in enumerate(retrieved_cast):
            report += f"**Chunk {i+1}:**\n```python\n{chunk}\n```\n"
            
        report += "\n**Agent Review (cAST):**\n"
        comments_cast = bug_expert.review(snippet, retrieved_cast)
        if not comments_cast:
            report += "- No issues found.\n"
        else:
            for c in comments_cast:
                report += f"{c}\n"
                
        report += "\n---\n"
        
    with open(OUTPUT_FILE, "w") as f:
        f.write(report)
        
    print(f"Experiment complete. Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_experiment()
