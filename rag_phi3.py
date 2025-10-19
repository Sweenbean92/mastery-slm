import os
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
import chromadb
from chromadb.utils import embedding_functions

# Initialize Ollama model (without streaming parameter)
ollama = Ollama(model="Mastery")  # Ensure the model name is correct

# Load embedding model
client = chromadb.PersistentClient(path="chroma_db")

# Use a small embedding model
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedder
)

def load_documents_from_folder(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if filename.endswith(".txt"):  # Process .txt files
            with open(file_path, "r", encoding="utf-8") as file:
                documents.append(file.read())
        
        elif filename.endswith(".pdf"):  # Process .pdf files using PyPDFLoader
            try:
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                pdf_text = " ".join(page.page_content for page in pages)  # Combine all pages
                documents.append(pdf_text)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return documents

def add_documents(documents):
    for i, doc in enumerate(documents):
        doc_id = str(i)  # Generate a unique ID for each document
        collection.upsert(
            documents=[doc],
            ids=[doc_id]
        )
        print(f"Added document with ID: {doc_id}")

#folder_path = "docs"  # Replace with your folder path
#documents = load_documents_from_folder(folder_path)
#add_documents(documents)
#doc_embeddings = embedder.encode(documents)

def retrieve(query, top_k=1):
    """
    Retrieve the most relevant documents from ChromaDB based on the query.

    Args:
        query (str): The user's query.
        top_k (int): The number of top documents to retrieve.

    Returns:
        list of str: The most relevant documents.
    """
    results = collection.query(
        query_texts=[query],  # ChromaDB will embed this query internally
        n_results=top_k,      # Number of results to return
        include=["documents"] # Include the document content in the results
    )
    return results["documents"][0]  # Return the list of top documents


def rag_ask_streaming(query):
    """
    Perform a retrieval-augmented generation (RAG) query with streaming support.

    Args:
        query (str): The user's query.
    """
    # Retrieve the most relevant documents from ChromaDB
    retrieved_docs = retrieve(query, top_k=2)
    context = "\n".join(retrieved_docs)
    prompt = f"Use the following context to answer the question. Context: {context} \n Question: {query} \nAnswer:"

    # Stream the response from the Ollama model
    print("Answer (streaming): ", end="", flush=True)
    try:
        for chunk in ollama.stream(prompt):  # Stream response chunks
            print(chunk, end="", flush=True)
    except AttributeError:
        print("\nStreaming is not supported by this Ollama implementation.")
    print()  # Add a newline after the response

if __name__ == "__main__":
    user_query = "Who is Albert Einstein?"
    rag_ask_streaming(user_query)