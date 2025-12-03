from typing import List
from .chunk import UniversalChunk

class ConceptExtractor:
    """Extracts initial UniversalChunks from AST."""
    
    def extract(self, node, code) -> List[UniversalChunk]:
        """
        Traverse AST and extract initial chunks based on semantic concepts.
        """
        chunks = []
        
        # Define relevant node types
        definitions = ["function_definition", "class_definition"]
        comments = ["comment"]
        
        # If node is a definition, create a chunk and return
        if node.type in definitions:
            chunks.append(self._create_chunk(node, code, "DEFINITION"))
            return chunks
            
        # If node is a comment
        if node.type in comments:
            chunks.append(self._create_chunk(node, code, "COMMENT"))
            return chunks

        # For other nodes (module, block, etc.), recurse
        # If it's a leaf node that is significant, treat as BLOCK
        if not node.children and node.type not in ["module", "block"]:
             # Filter out punctuation
             if node.type not in [":", "(", ")", "[", "]", "{", "}", "=", ",", "."]:
                 chunks.append(self._create_chunk(node, code, "BLOCK"))
             return chunks

        for child in node.children:
            chunks.extend(self.extract(child, code))
            
        return chunks

    def _create_chunk(self, node, code, concept):
        name = "context_block"
        if concept == "DEFINITION":
            name = self._get_node_name(node, code)
            
        return UniversalChunk(
            concept=concept,
            name=name,
            content=code[node.start_byte:node.end_byte],
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            metadata={"type": node.type}
        )

    def _get_node_name(self, node, code):
        for child in node.children:
            if child.type == "identifier":
                return code[child.start_byte:child.end_byte]
        return "unknown"
