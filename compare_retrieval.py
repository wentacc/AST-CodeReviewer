import os
import shutil
import glob
from ast_reviewer.agents.experts import BugExpert, SecurityExpert, StyleExpert
from ast_reviewer.retrieval.cast.pipeline import CASTChunker
from ast_reviewer.retrieval.vector_store import VectorStore

# Configuration
DATA_DIR = "./data/python-commits/merged"
OUTPUT_FILE = "comparison_report.md"
NUM_SAMPLES = 3

def load_samples(n=3):
    """Load n random samples from the merged directory."""
    # Pattern: *-commit.txt
    commit_files = glob.glob(os.path.join(DATA_DIR, "*-commit.txt"))
    # Sort for reproducibility or pick first n
    commit_files.sort()
    selected_commits = commit_files[:n]
    
    samples = []
    for commit_path in selected_commits:
        base_name = commit_path.replace("-commit.txt", "")
        context_path = base_name + "-context.txt"
        
        with open(commit_path, "r") as f:
            commit_diff = f.read()
            
        context_code = ""
        if os.path.exists(context_path):
            with open(context_path, "r") as f:
                context_code = f.read()
                
        samples.append({
            "id": os.path.basename(base_name),
            "diff": commit_diff,
            "context_code": context_code
        })
    return samples

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

    samples = load_samples(NUM_SAMPLES)
    
    report = "# Retrieval vs No Retrieval Comparison\n\n"
    
    for i, sample in enumerate(samples):
        print(f"Processing Sample {i+1}/{NUM_SAMPLES}: {sample['id']}")
        report += f"## Sample {i+1}: {sample['id']}\n\n"
        
        # 1. Index Context
        print("  Indexing context...")
        vector_store.clear() # Clear for each sample to simulate repo-specific context
        if sample["context_code"]:
            # Write context to temp file for chunker (chunker expects file path)
            with open("temp_context.py", "w") as f:
                f.write(sample["context_code"])
            
            try:
                chunks = chunker.chunk_file("temp_context.py")
                vector_store.add_chunks(chunks)
            except Exception as e:
                print(f"  Error chunking context: {e}")
        
        # 2. Retrieve
        print("  Retrieving...")
        # Simple query using the diff (in production we'd extract keywords)
        query = sample["diff"][:500] 
        retrieved_chunks = vector_store.query(query, n_results=3)
        
        # 3. Run Agents
        for expert in experts:
            print(f"  Running {expert.name}...")
            report += f"### {expert.name}\n"
            
            # Scenario A: No Retrieval
            report += "**Without Retrieval:**\n"
            comments_no_rag = expert.review(sample["diff"], [])
            if not comments_no_rag:
                report += "- No issues found.\n"
            else:
                for c in comments_no_rag:
                    report += f"{c}\n"
            
            # Scenario B: With Retrieval
            report += "\n**With Retrieval:**\n"
            comments_rag = expert.review(sample["diff"], retrieved_chunks)
            if not comments_rag:
                report += "- No issues found.\n"
            else:
                for c in comments_rag:
                    report += f"{c}\n"
            
            report += "\n---\n"
            
    with open(OUTPUT_FILE, "w") as f:
        f.write(report)
        
    print(f"Comparison complete. Report saved to {OUTPUT_FILE}")
    
    # Cleanup
    if os.path.exists("temp_context.py"):
        os.remove("temp_context.py")

if __name__ == "__main__":
    run_comparison()
