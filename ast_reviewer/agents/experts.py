from typing import List, Dict
#from langchain_ollama.llms import OllamaLLM
#from langchain_core.prompts import ChatPromptTemplate
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel

class BaseExpert:
    def __init__(self, name: str, role_description: str, lora_path: str = None):
        self.name = name
        self.role_description = role_description
        # Initialize gamma-3-4b-it
        base_model_id = "google/gemma-3-4b-it"

        print(f"[{self.name}] Loading base model: {base_model_id}")

        # Load base model
        tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            device_map="auto",
            torch_dtype="auto",
        )

        # --------------------------------------------
        # Load LoRA adapter (if provided)
        # --------------------------------------------
        if lora_path:
            print(f"[{self.name}] Loading LoRA adapter from: {lora_path}")
            model = PeftModel.from_pretrained(model, lora_path)
        else:
            print(f"[{self.name}] Using original Gemma-3-4B-IT model")

        self.pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device_map="auto",
            torch_dtype="auto",
            max_new_tokens=512,
        )

        #self.model = OllamaLLM(model='llama3.2')
        
        self.template = """
You are a specialized code review expert focusing ONLY on {role}.

Here is the code snippet to review:
```python
{code}
```

Additional Context (Related Code):
{context}

Your task:
1. Identify any issues related specifically to **{role}**.
2. If there are NO issues related to {role}, reply with "No issues found."
3. Be concise and actionable. Do not provide general feedback outside your scope.
4. Format your response as a bulleted list of issues if any are found.

Review:
"""
    def generate(self, prompt: str) -> str:
        """Generate text using Gemma-3 model."""
        output = self.pipe(prompt, do_sample=False)[0]["generated_text"]
        # Strip prompt from output
        return output[len(prompt):].strip()
    
    def review(self, diff: str, context: List[Dict]) -> List[str]:
        """
        Reviews the code snippet and returns bullet-point comments.
        """
        try:
            # Format context chunks
            context_str = ""
            if context:
                context_str = "\n".join(
                    [f"--- Chunk: {c['metadata']['name']} ---\n{c['content']}\n"
                    for c in context]
                )

            # Build prompt
            prompt = self.template.format(
                role=self.role_description,
                code=diff,
                context=context_str
            )

            # Run model
            response = self.generate(prompt)

            # Parse model response
            comments = []
            if "No issues found" in response or not response.strip():
                return []

            for line in response.split("\n"):
                clean = line.strip()
                if clean.startswith("- ") or clean.startswith("* ") or clean.startswith("1. "):
                    comments.append(clean)

            # fallback
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
