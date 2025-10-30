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
        prompt = f"Use the following context to answer the question. Context: {context} \n Question: {query} \nAnswer:"

        print("Answer (streaming): ", end="", flush=True)
        try:
            for chunk in self.ollama.stream(prompt):
                print(chunk, end="", flush=True)
        except AttributeError:
            print("\nStreaming is not supported by this Ollama implementation.")
        print()

if __name__ == "__main__":
    # Initialize the RAG chain with default model
    rag = RAGChain(model_name="phi")
    
    # Example of switching between models and asking questions
    while True:
        print("\n1. Ask a question")
        print("2. Switch model")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            query = input("Enter your question: ")
            if query.strip():
                rag.rag_ask_streaming(query)
        elif choice == "2":
            new_model = input("Enter model name (e.g., smol, phi, gemma): ")
            rag.switch_model(new_model)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")