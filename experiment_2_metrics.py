import os
import ast
import glob
import re
from ast_reviewer.retrieval.cast.pipeline import CASTChunker
from ast_reviewer.retrieval.standard_chunker import StandardChunker
from ast_reviewer.retrieval.vector_store import VectorStore

# Configuration
GENERATED_DIR = "./generated_projects"
SNIPPET_SIZE = 30
TOP_K = 3
METRICS_OUTPUT_FILE = "experiment_2_metrics.md"

def get_snippet(code, num_lines=SNIPPET_SIZE):
    lines = code.splitlines()
    if len(lines) <= num_lines:
        return code
    start = len(lines) // 3
    end = start + num_lines
    return "\n".join(lines[start:end])

import textwrap

def is_syntactically_complete(code_chunk):
    """Check if the code chunk is a valid AST (parseable)."""
    try:
        # Dedent to handle methods/inner classes
        dedented_code = textwrap.dedent(code_chunk)
        ast.parse(dedented_code)
        return True
    except SyntaxError:
        return False

def extract_identifiers(code):
    """Extract variable/function/class names used in the code."""
    identifiers = set()
    try:
        # Dedent snippet to ensure it parses
        tree = ast.parse(textwrap.dedent(code))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                identifiers.add(node.id)
            elif isinstance(node, ast.Attribute):
                identifiers.add(node.attr)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    identifiers.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    identifiers.add(node.func.attr)
    except SyntaxError:
        # Fallback to regex if snippet is partial
        # 1. Find potential function calls: word(
        calls = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', code)
        identifiers.update(calls)
        
        # 2. Find potential attribute access: .word
        attrs = re.findall(r'\.([a-zA-Z_]\w*)', code)
        identifiers.update(attrs)
        
        # 3. Find ALL words, but filter aggressively
        all_words = re.findall(r'\b[a-zA-Z_]\w*\b', code)
        stopwords = {"if", "else", "for", "while", "return", "def", "class", "import", "from", "as", "pass", "try", "except", "raise", "with", "in", "is", "not", "and", "or", "None", "True", "False", "self", "the", "a", "an", "to", "of", "and", "in", "is", "it", "you", "that", "he", "was", "for", "on", "are", "as", "with", "his", "they", "I", "at", "be", "this", "have", "from", "or", "one", "had", "by", "word", "but", "not", "what", "all", "were", "we", "when", "your", "can", "said", "there", "use", "an", "each", "which", "she", "do", "how", "their", "if", "will", "up", "other", "about", "out", "many", "then", "them", "these", "so", "some", "her", "would", "make", "like", "him", "into", "time", "has", "look", "two", "more", "write", "go", "see", "number", "no", "way", "could", "people", "my", "than", "first", "water", "been", "call", "who", "oil", "its", "now", "find"}
        
        for w in all_words:
            if w not in stopwords and len(w) > 2:
                # Heuristic: Code often uses underscores or CamelCase
                if "_" in w or (w[0].isupper() and not w.isupper()): 
                    identifiers.add(w)
                # Or if it's already found as a call/attr, keep it
                elif w in identifiers:
                    pass
                # Otherwise, be conservative and maybe skip "plain" words?
                # Let's keep them if they are not stopwords, but maybe the embedding handles them?
                # Actually, let's just use the stopword filter.
                else:
                    identifiers.add(w)
    return identifiers

def find_definitions(full_code, identifiers, snippet):
    """Find lines where identifiers are defined in the full code, EXCLUDING the snippet."""
    definitions = {} # id -> list of lines
    lines = full_code.splitlines()
    snippet_lines = set(snippet.splitlines())
    
    for i, line in enumerate(lines):
        if line.strip() in snippet_lines:
            continue # Skip definitions inside the snippet itself
            
        for ident in identifiers:
            # Focus on major definitions: functions and classes
            # Strict regex to avoid matching partial words
            if re.search(rf'^\s*(def|class)\s+{ident}\b', line):
                if ident not in definitions:
                    definitions[ident] = []
                definitions[ident].append(line)
    return definitions

def calculate_recall(retrieved_chunks, definitions):
    """
    Calculate how many of the required definitions were retrieved.
    Recall = (Definitions Found in Chunks) / (Total Definitions Needed)
    """
    if not definitions:
        return None # N/A
        
    found_count = 0
    total_needed = len(definitions)
    
    for ident, def_lines in definitions.items():
        found = False
        for chunk in retrieved_chunks:
            for def_line in def_lines:
                if def_line.strip() in chunk['content']:
                    found = True
                    break
            if found: break
        if found:
            found_count += 1
            
    return found_count / total_needed

def run_metrics(
    generated_dir: str = GENERATED_DIR,
    snippet_size: int = SNIPPET_SIZE,
    top_k: int = TOP_K,
    output_file: str = METRICS_OUTPUT_FILE,
    quiet: bool = False,
):
    if not quiet:
        print("Running Quantitative Analysis for Experiment 2 (Refined)...")
    
    files = glob.glob(os.path.join(generated_dir, "*.py"))
    files.sort()
    if not files:
        raise FileNotFoundError(f"No .py files found under {generated_dir}")
    
    cast_chunker = CASTChunker()
    std_chunker = StandardChunker(chunk_size=600, overlap=50)
    vector_store = VectorStore()
    
    results = {
        "std": {"completeness": [], "recall": []},
        "cast": {"completeness": [], "recall": []}
    }
    
    for file_path in files:
        # print(f"Processing {os.path.basename(file_path)}...")
        with open(file_path, "r") as f:
            full_code = f.read()
            
        snippet = get_snippet(full_code, num_lines=snippet_size)
        identifiers = extract_identifiers(snippet)
        definitions = find_definitions(full_code, identifiers, snippet)
        
        # --- Standard ---
        vector_store.clear()
        chunks = std_chunker.chunk_file(file_path)
        vector_store.add_chunks(chunks)
        retrieved_std = vector_store.query(snippet, n_results=top_k)
        
        # Completeness
        comp_score = sum(1 for c in retrieved_std if is_syntactically_complete(c['content'])) / len(retrieved_std) if retrieved_std else 0
        results["std"]["completeness"].append(comp_score)
        
        # Recall
        rec_score = calculate_recall(retrieved_std, definitions)
        if rec_score is not None:
            results["std"]["recall"].append(rec_score)
        
        # --- cAST ---
        vector_store.clear()
        try:
            chunks = cast_chunker.chunk_file(file_path)
            vector_store.add_chunks(chunks)
            
            # Query Expansion: Append identifiers to help dense retrieval find definitions
            expanded_query = snippet + "\n\nKeywords: " + " ".join(identifiers)
            if not quiet and "sample_10.py" in file_path:
                print(f"DEBUG: Identifiers: {identifiers}")
                print(f"DEBUG: Expanded Query: {expanded_query[:100]}...")
            retrieved_cast = vector_store.query(expanded_query, n_results=top_k)
            
            # Completeness
            comp_score = sum(1 for c in retrieved_cast if is_syntactically_complete(c['content'])) / len(retrieved_cast) if retrieved_cast else 0
            results["cast"]["completeness"].append(comp_score)
            
            # Recall
            rec_score = calculate_recall(retrieved_cast, definitions)
            if rec_score is not None:
                results["cast"]["recall"].append(rec_score)
            
        except Exception as e:
            print(f"Skipping cAST for {file_path} due to error: {e}")

    # Aggregate
    if results["std"]["completeness"]:
        avg_std_comp = sum(results["std"]["completeness"]) / len(results["std"]["completeness"]) * 100
    else: avg_std_comp = 0
    
    if results["std"]["recall"]:
        avg_std_rec = sum(results["std"]["recall"]) / len(results["std"]["recall"]) * 100
    else: avg_std_rec = 0
    
    if results["cast"]["completeness"]:
        avg_cast_comp = sum(results["cast"]["completeness"]) / len(results["cast"]["completeness"]) * 100
    else: avg_cast_comp = 0
    
    if results["cast"]["recall"]:
        avg_cast_rec = sum(results["cast"]["recall"]) / len(results["cast"]["recall"]) * 100
    else: avg_cast_rec = 0
    
    report = f"""
# Experiment 2 Quantitative Results (Refined)

## Syntactic Completeness
(Percentage of retrieved chunks that are valid, parseable code blocks)
- Standard RAG: {avg_std_comp:.2f}%
- cAST RAG:     {avg_cast_comp:.2f}%

## Definition Recall@{top_k}
(Percentage of identifiers in the snippet whose definitions were successfully retrieved)
- Standard RAG: {avg_std_rec:.2f}%
- cAST RAG:     {avg_cast_rec:.2f}%
"""
    if not quiet:
        print(report)

    if output_file:
        with open(output_file, "w") as f:
            f.write(report)

    return {
        "report": report,
        "averages": {
            "std": {"completeness": avg_std_comp, "recall": avg_std_rec},
            "cast": {"completeness": avg_cast_comp, "recall": avg_cast_rec},
        },
        "top_k": top_k,
        "output_file": output_file,
    }

if __name__ == "__main__":
    run_metrics()
