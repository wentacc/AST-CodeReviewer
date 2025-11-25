from typing import List, Dict
from ast_reviewer.retrieval.cast_chunker import CASTChunker
from ast_reviewer.agents.router import RouterAgent
from ast_reviewer.agents.experts import SecurityExpert, StyleExpert, DocExpert, BugExpert

class ReviewPipeline:
    def __init__(self):
        self.chunker = CASTChunker()
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
            chunks = self.chunker.chunk_file(file_path)
        except Exception as e:
            return f"Error chunking file: {e}"

        all_comments = []

        # 2. Review each chunk (simulating diff review)
        for chunk in chunks:
            # In a real scenario, we'd compare against previous version to get diff
            # Here we just treat the chunk content as the "diff" for prototype purposes
            diff = chunk['content']
            context = [] # Retrieve context using vector store (omitted for prototype)

            # 3. Routing
            selected_experts = self.router.route(diff, context)
            
            # 4. Expert Review
            for expert_name in selected_experts:
                if expert_name in self.experts:
                    comments = self.experts[expert_name].review(diff, context)
                    for comment in comments:
                        all_comments.append({
                            "file": file_path,
                            "line": chunk['start_line'] + 1, # Approximate line
                            "expert": expert_name,
                            "message": comment
                        })

        # 5. Aggregation & Formatting
        return self._format_report(all_comments)

    def _format_report(self, comments: List[Dict]) -> str:
        if not comments:
            return "No issues found."
        
        report = "AST-Reviewer Report\n===================\n\n"
        for c in comments:
            report += f"[{c['expert']}] {c['file']}:{c['line']}\n"
            report += f"  {c['message']}\n\n"
        return report
