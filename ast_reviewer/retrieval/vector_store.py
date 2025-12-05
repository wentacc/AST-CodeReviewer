import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
import os

class VectorStore:
    def __init__(self, collection_name="ast_reviewer_context"):
        # Use persistent client to save data to disk
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Use default embedding function for simplicity in prototype
        # In production, we would use OpenAI or a local model via Ollama
        # For now, let's use the default SentenceTransformer (all-MiniLM-L6-v2) 
        # that Chroma provides if no function is specified.
        # Note: This requires 'sentence-transformers' which is usually installed with chromadb default
        # Use all-mpnet-base-v2 for better semantic retrieval
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_chunks(self, chunks: List[Dict]):
        """
        Adds chunks to the vector store.
        """
        if not chunks:
            return

        documents = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            # Create a unique ID
            chunk_id = f"{chunk['name']}_{chunk['start_line']}_{i}"
            
            documents.append(chunk['content'])
            metadatas.append({
                "name": chunk['name'],
                "type": chunk['type'],
                "start_line": chunk['start_line'],
                "end_line": chunk['end_line']
            })
            ids.append(chunk_id)

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 3) -> List[Dict]:
        """
        Queries the vector store for relevant chunks.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
                
        return formatted_results

    def clear(self):
        """Clears the collection"""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            embedding_function=self.embedding_fn
        )
