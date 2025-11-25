from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model='llama3.2')

template = """
You are an expert in reviewing code.

Here is the code snippet:
{code}

Review the code and provide feedback on the following aspects:
1. Code quality and best practices
2. Security vulnerabilities
3. Performance issues
4. Maintainability
5. Compliance with coding standards

Provide specific examples and recommendations for improvement.

"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

result = chain.invoke({"code": "import os\nos.environ['OPENAI_API_KEY'] = 'your-api-key'\nimport openai\nopenai.api_key = os.environ['OPENAI_API_KEY']\nresponse = openai.Completion.create(model='gpt-3.5-turbo', prompt='Hello, how are you?')"})
print(result)