import os
import shutil
import glob
from ast_reviewer.agents.experts import BugExpert, SecurityExpert, StyleExpert
from ast_reviewer.retrieval.cast.pipeline import CASTChunker
from ast_reviewer.retrieval.vector_store import VectorStore

# Configuration
GENERATED_DIR = "./generated_projects"
OUTPUT_FILE = "comparison_report_generated.md"
SNIPPET_SIZE = 30  # Number of lines for the "diff"

def load_generated_samples():
    files = glob.glob(os.path.join(GENERATED_DIR, "*.py"))
    files.sort()
    return files

def get_snippet(code, num_lines=SNIPPET_SIZE):
    lines = code.splitlines()
    if len(lines) <= num_lines:
        return code
    
    # Take a chunk from the middle to likely hit some logic dependent on imports or classes
    start = len(lines) // 3
    end = start + num_lines
    return "\n".join(lines[start:end])

def run_comparison():
    print("Initializing Agents and Pipeline...")
    # Agents
    bug_expert = BugExpert()
    security_expert = SecurityExpert()
    style_expert = StyleExpert()
    experts = [bug_expert, security_expert, style_expert]
    
    # Retrieval
    chunker = CASTChunker()
    
    # Clean DB
    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db")
    vector_store = VectorStore()

    samples = load_generated_samples()
    
    report = "# Retrieval vs No Retrieval Comparison (Generated Projects)\n\n"
    report += "Methodology: The full file is indexed as context. A snippet (approx 30 lines) from the middle of the file is presented as the 'diff' to review.\n\n"
    
    for i, file_path in enumerate(samples):
        filename = os.path.basename(file_path)
        print(f"Processing Sample {i+1}/{len(samples)}: {filename}")
        
        with open(file_path, "r") as f:
            full_code = f.read()
            
        snippet = get_snippet(full_code)
        
        report += f"## Sample {i+1}: {filename}\n\n"
        report += "### Snippet Reviewed\n"
        report += f"```python\n{snippet}\n```\n\n"
        
        # 1. Index Context (Full File)
        print("  Indexing context...")
        vector_store.clear()
        
        # Use the file directly for chunking
        try:
            chunks = chunker.chunk_file(file_path)
            vector_store.add_chunks(chunks)
        except Exception as e:
            print(f"  Error chunking context: {e}")
            report += f"> Error indexing context: {e}\n\n"
        
        # 2. Retrieve
        print("  Retrieving...")
        query = snippet
        retrieved_chunks = vector_store.query(query, n_results=3)
        
        # 3. Run Agents
        for expert in experts:
            print(f"  Running {expert.name}...")
            report += f"### {expert.name}\n"
            
            # Scenario A: No Retrieval
            report += "**Without Retrieval:**\n"
            comments_no_rag = expert.review(snippet, [])
            if not comments_no_rag:
                report += "- No issues found.\n"
            else:
                for c in comments_no_rag:
                    report += f"{c}\n"
            
            # Scenario B: With Retrieval
            report += "\n**With Retrieval:**\n"
            comments_rag = expert.review(snippet, retrieved_chunks)
            if not comments_rag:
                report += "- No issues found.\n"
            else:
                for c in comments_rag:
                    report += f"{c}\n"
            
            report += "\n---\n"
            
    with open(OUTPUT_FILE, "w") as f:
        f.write(report)
        
    print(f"Comparison complete. Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_comparison()
