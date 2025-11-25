# AST-Reviewer

AST-Reviewer is a trust-centric Automated Code Review (ACR) agent designed to minimize false positives by using structure-aware retrieval and specialized expert models.

## Features

-   **Structure-Aware Retrieval (cAST)**: Uses `tree-sitter` to chunk code by semantic units (functions, classes) rather than arbitrary lines.
-   **Mixture-of-Prompts (MoP)**: Routes code chunks to specialized "Expert Agents" (Security, Style, Documentation, Bug) based on content.
-   **Extensible Architecture**: Easy to add new experts or swap out the routing logic.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/ast-reviewer.git
    cd ast-reviewer
    ```

2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the reviewer on a file:

```bash
python3 -m ast_reviewer.main path/to/your/file.py
```

### Example

```bash
python3 -m ast_reviewer.main sample_code.py
```

Output:
```
Reviewing sample_code.py...

AST-Reviewer Report
===================

[SecurityExpert] sample_code.py:3
  [Security] Do not hardcode passwords.
...
```

## Project Structure

-   `ast_reviewer/`: Main package.
    -   `retrieval/`: cAST chunking logic.
    -   `agents/`: Router and Expert agent implementations.
    -   `pipeline/`: Orchestration logic.
-   `sample_code.py`: Example file for testing.

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Commit your changes.
4.  Push to the branch.
5.  Open a Pull Request.

## License

[MIT](LICENSE)
