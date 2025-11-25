import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import os

class CASTChunker:
    def __init__(self):
        self.PY_LANGUAGE = Language(tspython.language())
        self.parser = Parser(self.PY_LANGUAGE)

    def parse(self, code):
        return self.parser.parse(bytes(code, "utf8"))

    def chunk_file(self, file_path):
        with open(file_path, "r") as f:
            code = f.read()
        
        tree = self.parse(code)
        chunks = []
        
        self._traverse_tree(tree.root_node, code, chunks)
                
        return chunks

    def _traverse_tree(self, node, code, chunks):
        if node.type in ["function_definition", "class_definition"]:
            chunks.append({
                "type": node.type,
                "name": self._get_node_name(node, code),
                "content": code[node.start_byte:node.end_byte],
                "start_line": node.start_point[0],
                "end_line": node.end_point[0]
            })
            # Don't traverse children of a chunk we just added to avoid duplicates
            return

        for child in node.children:
            self._traverse_tree(child, code, chunks)

    def _get_node_name(self, node, code):
        # Helper to extract name from function/class definition
        for child in node.children:
            if child.type == "identifier":
                return code[child.start_byte:child.end_byte]
        return "unknown"

if __name__ == "__main__":
    # Test
    chunker = CASTChunker()
    code = """
def foo():
    print("bar")

class MyClass:
    def method(self):
        pass
"""
    tree = chunker.parse(code)
    print(tree.root_node)
    print(chunker.parse(code).root_node)
    chunks = chunker.chunk_file("ast_reviewer/retrieval/cast_chunker.py") # Test on itself
    print(f"Found {len(chunks)} chunks")
    for chunk in chunks:
        print(f"- {chunk['type']}: {chunk['name']}")
