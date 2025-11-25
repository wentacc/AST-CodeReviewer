from typing import List, Dict
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

class BaseExpert:
    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description
        # Initialize Ollama model (assuming llama3.2 is available)
        self.model = OllamaLLM(model='llama3.2')
        
        self.template = """
You are a specialized code review expert focusing ONLY on {role}.

Here is the code snippet to review:
```python
{code}
```

Your task:
1. Identify any issues related specifically to **{role}**.
2. If there are NO issues related to {role}, reply with "No issues found."
3. Be concise and actionable. Do not provide general feedback outside your scope.
4. Format your response as a bulleted list of issues if any are found.

Review:
"""
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.chain = self.prompt | self.model

    def review(self, diff: str, context: List[Dict]) -> List[str]:
        """
        Reviews the code using the LLM and returns a list of comments.
        """
        try:
            # Invoke the chain
            response = self.chain.invoke({"role": self.role_description, "code": diff})
            
            # Parse response (simple splitting for prototype)
            comments = []
            if "No issues found" in response or not response.strip():
                return []
            
            lines = response.split('\n')
            for line in lines:
                clean_line = line.strip()
                if clean_line.startswith('- ') or clean_line.startswith('* ') or clean_line.startswith('1. '):
                    comments.append(clean_line)
            
            # If no list items found but text exists, return the whole text as one comment
            if not comments and response.strip():
                comments.append(response.strip())
                
            return comments
        except Exception as e:
            return [f"Error during LLM review: {str(e)}"]

class SecurityExpert(BaseExpert):
    def __init__(self):
        super().__init__(
            "SecurityExpert", 
            "Security Vulnerabilities (e.g., injection, hardcoded secrets, unsafe execution, weak cryptography)"
        )

class StyleExpert(BaseExpert):
    def __init__(self):
        super().__init__(
            "StyleExpert", 
            "Code Style and Readability (e.g., naming conventions, indentation, PEP8 compliance, clarity)"
        )

class DocExpert(BaseExpert):
    def __init__(self):
        super().__init__(
            "DocExpert", 
            "Documentation and Comments (e.g., missing docstrings, unclear comments, outdated documentation)"
        )

class BugExpert(BaseExpert):
    def __init__(self):
        super().__init__(
            "BugExpert", 
            "Logic Bugs and Correctness (e.g., off-by-one errors, infinite loops, incorrect conditions, variable misuse)"
        )
