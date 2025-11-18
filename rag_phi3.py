import os
from langchain_community.llms import Ollama
import chromadb

class RAGChain:
    def __init__(self, model_name="Phi"):
        self.model_name = model_name
        self.ollama = Ollama(model=model_name)
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="documents",
        )
    
    def switch_model(self, new_model_name):
        """Switch to a different Ollama model"""
        self.model_name = new_model_name
        self.ollama = Ollama(model=new_model_name)
        print(f"Switched to model: {new_model_name}")

    def retrieve(self, query, top_k=1):
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents"]
        )
        return results["documents"][0]

    def rag_ask_streaming(self, query):
        retrieved_docs = self.retrieve(query, top_k=2)
        context = "\n".join(retrieved_docs)
        prompt = f"Use the following context to answer the question concisely. Context: {context} \n Question: {query} \nAnswer:"

        print("Answer (streaming): ", end="", flush=True)
        try:
            for chunk in self.ollama.stream(prompt):
                print(chunk, end="", flush=True)
        except AttributeError:
            print("\nStreaming is not supported by this Ollama implementation.")
        print()