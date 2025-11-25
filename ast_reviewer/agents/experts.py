from typing import List, Dict

class BaseExpert:
    def __init__(self, name: str):
        self.name = name

    def review(self, diff: str, context: List[Dict]) -> List[str]:
        """
        Reviews the code and returns a list of comments.
        """
        raise NotImplementedError

class SecurityExpert(BaseExpert):
    def __init__(self):
        super().__init__("SecurityExpert")

    def review(self, diff: str, context: List[Dict]) -> List[str]:
        comments = []
        # Mock logic
        if "eval(" in diff:
            comments.append("[Security] Avoid using eval(), it is dangerous.")
        if "password =" in diff:
            comments.append("[Security] Do not hardcode passwords.")
        return comments

class StyleExpert(BaseExpert):
    def __init__(self):
        super().__init__("StyleExpert")

    def review(self, diff: str, context: List[Dict]) -> List[str]:
        comments = []
        # Mock logic
        if "    " not in diff and "\t" in diff:
            comments.append("[Style] Use spaces instead of tabs.")
        if "VAR =" in diff:
             comments.append("[Style] Variable names should be lowercase.")
        return comments

class DocExpert(BaseExpert):
    def __init__(self):
        super().__init__("DocExpert")

    def review(self, diff: str, context: List[Dict]) -> List[str]:
        comments = []
        # Mock logic
        if "def " in diff and "\"\"\"" not in diff:
            comments.append("[Doc] Missing docstring for function.")
        return comments

class BugExpert(BaseExpert):
    def __init__(self):
        super().__init__("BugExpert")

    def review(self, diff: str, context: List[Dict]) -> List[str]:
        comments = []
        # Mock logic
        if "if x = 5" in diff:
            comments.append("[Bug] Assignment in condition (use ==).")
        return comments
