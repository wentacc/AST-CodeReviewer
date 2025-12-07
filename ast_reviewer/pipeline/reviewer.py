from typing import List, Dict
from ast_reviewer.retrieval.cast import CASTChunker
from ast_reviewer.retrieval.vector_store import VectorStore
from ast_reviewer.agents.router import RouterAgent
from ast_reviewer.agents.experts import SecurityExpert, StyleExpert, DocExpert, BugExpert
import os

class ReviewPipeline:
    def __init__(self):
        self.chunker = CASTChunker()
        self.vector_store = VectorStore()
        self.router = RouterAgent()
        self.experts = {
            "SecurityExpert": SecurityExpert(),
            "StyleExpert": StyleExpert(),
            "DocExpert": DocExpert(),
            "BugExpert": BugExpert()
        }

    def review_file(self, file_path: str) -> str:
        # 1. Chunking
        try:
            print(f"Chunking {file_path}...")
            chunks = self.chunker.chunk_file(file_path)
        except Exception as e:
            return f"Error chunking file: {e}"

        # 2. Indexing (In a real scenario, we'd index the whole repo beforehand)
        # For this prototype, we'll clear and index the current file + maybe others if we had them
        print("Indexing chunks...")
        self.vector_store.clear()
        self.vector_store.add_chunks(chunks)

        all_comments = []

        # 3. Review each chunk
        print("Reviewing chunks...")
        for chunk in chunks:
            diff = chunk['content']
            
            # Retrieve context (find similar chunks in the store - e.g. related functions)
            # We exclude the chunk itself from context ideally, but for now we just query
            context = self.vector_store.query(diff, n_results=3)
            
            # Filter out the chunk itself from context if it appears
            filtered_context = [
                c for c in context 
                if c['metadata']['name'] != chunk['name'] or c['metadata']['start_line'] != chunk['start_line']
            ]

            # 4. Routing
            selected_experts = self.router.route(diff, filtered_context)
            print(f"  - Chunk '{chunk['name']}' routed to: {selected_experts}")
            
            # 5. Expert Review
            for expert_name in selected_experts:
                if expert_name in self.experts:
                    comments = self.experts[expert_name].review(diff, filtered_context)
                    for comment in comments:
                        all_comments.append({
                            "file": file_path,
                            "line": chunk['start_line'] + 1, # Approximate line
                            "expert": expert_name,
                            "message": comment
                        })

        # 6. Aggregation & Formatting
        return self._format_report(all_comments)

    def _format_report(self, comments: List[Dict]) -> str:
        if not comments:
            return "No issues found."
        
        report = "AST-Reviewer Report\n===================\n\n"
        
        # Group by file and line
        sorted_comments = sorted(comments, key=lambda x: (x['file'], x['line']))
        
        for c in sorted_comments:
            report += f"[{c['expert']}] {c['file']}:{c['line']}\n"
            report += f"  {c['message']}\n\n"
        return report
