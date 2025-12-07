from typing import List, Dict
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json

class RouterAgent:
    def __init__(self):
        # Use a lightweight model for routing if possible, but we'll stick to llama3.2
        self.model = OllamaLLM(model='llama3.2')
        
        self.template = """
You are a Code Review Router. Your job is to analyze code changes and route them to the appropriate specialized experts.

Available Experts:
- SecurityExpert: Vulnerabilities, secrets, injection, unsafe ops.
- StyleExpert: Formatting, naming conventions, readability.
- DocExpert: Documentation, comments, docstrings.
- BugExpert: Logic errors, off-by-one, infinite loops, correctness.

Input Code:
```python
{diff}
```

Context:
{context}

Instructions:
1. Analyze the code and context.
2. Select ALL relevant experts.
3. Return ONLY a JSON list of expert names, e.g., ["SecurityExpert", "StyleExpert"].
4. Do not output any other text.
"""
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.chain = self.prompt | self.model

    def route(self, diff: str, context: List[Dict]) -> List[str]:
        """
        Analyzes the diff and context to select appropriate experts.
        Returns a list of expert names.
        """
        # Format context for prompt
        context_str = "\n".join([f"- {c['content'][:200]}..." for c in context]) if context else "No context."
        
        try:
            response = self.chain.invoke({"diff": diff, "context": context_str})
            
            # Clean response to ensure it's valid JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
                
            experts = json.loads(response)
            
            # Validate experts
            valid_experts = ["SecurityExpert", "StyleExpert", "DocExpert", "BugExpert"]
            return [e for e in experts if e in valid_experts]
            
        except Exception as e:
            print(f"Router Error: {e}. Falling back to keyword routing.")
            return self._fallback_route(diff)

    def _fallback_route(self, diff: str) -> List[str]:
        experts = []
        diff_lower = diff.lower()
        
        # Security
        if any(kw in diff_lower for kw in ["sql", "exec", "eval", "subprocess", "password", "secret", "auth"]):
            experts.append("SecurityExpert")
            
        # Style (always)
        experts.append("StyleExpert")
        
        # Doc
        if any(kw in diff_lower for kw in ["def ", "class ", "docstring", "\"\"\"", "'''"]):
            experts.append("DocExpert")
            
        # Bug
        if any(kw in diff_lower for kw in ["if", "for", "while", "return", "+", "-", "*", "/"]):
            experts.append("BugExpert")
            
        return list(set(experts))
