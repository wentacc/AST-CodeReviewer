import argparse
import os
import sys
from typing import List, Dict

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ast_reviewer.agents.experts import BugExpert, SecurityExpert, StyleExpert
from ast_reviewer.retrieval.cast.pipeline import CASTChunker
from ast_reviewer.retrieval.vector_store import VectorStore

def main():
    parser = argparse.ArgumentParser(description="AST-Based Code Reviewer with Retrieval")
    parser.add_argument("target", help="File or directory to review")
    parser.add_argument("--context", default=".", help="Directory to use for context retrieval (default: current dir)")
    parser.add_argument("--no-retrieval", action="store_true", help="Disable context retrieval")
    parser.add_argument("--clear-db", action="store_true", help="Clear the vector database before indexing")
    
    args = parser.parse_args()
    
    target_path = args.target
    if not os.path.exists(target_path):
        print(f"Error: Target '{target_path}' does not exist.")
        return

    # 1. Setup Retrieval
    vector_store = None
    if not args.no_retrieval:
        print(f"Initializing Retrieval Pipeline (Context: {args.context})...")
        vector_store = VectorStore()
        
        if args.clear_db:
            print("Clearing vector database...")
            vector_store.clear()
            
        # Check if we need to index
        # For simplicity in this prototype, we'll just index the target file's directory if it's not already indexed
        # In a real app, we'd have a more sophisticated index management
        chunker = CASTChunker()
        
        # If target is a file, read it to use as query
        query_text = ""
        if os.path.isfile(target_path):
            with open(target_path, "r") as f:
                query_text = f.read()
        else:
            # If directory, maybe just use the directory name or list of files?
            # For now, let's just say we review files individually
            pass 

        # Indexing (Simplified: Index the context directory)
        # Note: Indexing the whole repo might take time. 
        # For this demo, let's assume the user might want to index specific files or the DB is persistent.
        # We will index the 'context' directory if provided and not just '.' (unless explicitly asked)
        if args.context != ".":
             print(f"Indexing files in {args.context}...")
             # Walk and chunk
             for root, _, files in os.walk(args.context):
                 for file in files:
                     if file.endswith(".py"):
                         full_path = os.path.join(root, file)
                         try:
                             chunks = chunker.chunk_file(full_path)
                             vector_store.add_chunks(chunks)
                             print(f"  Indexed {file} ({len(chunks)} chunks)")
                         except Exception as e:
                             print(f"  Failed to index {file}: {e}")

    # 2. Run Review
    experts = [BugExpert(), SecurityExpert(), StyleExpert()]
    
    files_to_review = []
    if os.path.isfile(target_path):
        files_to_review.append(target_path)
    else:
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith(".py"):
                    files_to_review.append(os.path.join(root, file))
                    
    print(f"\nStarting Review for {len(files_to_review)} file(s)...\n")
    
    for file_path in files_to_review:
        print(f"=== Reviewing: {file_path} ===")
        with open(file_path, "r") as f:
            code_content = f.read()
            
        # Retrieve context
        retrieved_context = []
        if vector_store:
            # Query using the code content
            # Truncate query to avoid token limits in embedding model if necessary
            retrieved_context = vector_store.query(code_content[:1000])
            if retrieved_context:
                print(f"  [Context] Retrieved {len(retrieved_context)} related chunks.")
        
        for expert in experts:
            print(f"  Running {expert.name}...")
            comments = expert.review(code_content, retrieved_context)
            if comments:
                for comment in comments:
                    print(f"    - {comment}")
            else:
                print("    - No issues found.")
        print("\n")

if __name__ == "__main__":
    main()