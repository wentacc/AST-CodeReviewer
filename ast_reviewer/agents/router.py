from typing import List, Dict
import re

class RouterAgent:
    def __init__(self):
        # In a real implementation, this would use an LLM
        pass

    def route(self, diff: str, context: List[Dict]) -> List[str]:
        """
        Analyzes the diff and context to select appropriate experts.
        Returns a list of expert names.
        """
        experts = []
        
        # Simple keyword-based routing for prototype
        diff_lower = diff.lower()
        
        # Security Expert
        if any(kw in diff_lower for kw in ["sql", "exec", "eval", "subprocess", "password", "secret", "auth"]):
            experts.append("SecurityExpert")
            
        # Style Expert - almost always relevant
        experts.append("StyleExpert")
        
        # Doc Expert
        if any(kw in diff_lower for kw in ["def ", "class ", "docstring", "\"\"\"", "'''"]):
            experts.append("DocExpert")
            
        # Bug Expert - almost always relevant for logic changes
        if any(kw in diff_lower for kw in ["if", "for", "while", "return", "+", "-", "*", "/"]):
            experts.append("BugExpert")
            
        return list(set(experts))
