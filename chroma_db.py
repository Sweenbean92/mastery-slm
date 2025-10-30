import chromadb 
import os 
from langchain.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="chroma_db")

# Use a small embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

collection = client.get_or_create_collection(
    name="documents"
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

def add_documents(documents, base_id_prefix="doc"):
    ids = [f"{base_id_prefix}-{i}" for i in range(len(documents))]
    embeddings = embedder.encode(documents, convert_to_numpy=True)
    collection.upsert(
        documents=documents,
        ids=ids,
        embeddings=embeddings.tolist()
    )

folder_path = "docs"
documents = load_documents_from_folder(folder_path)
if documents:
    add_documents(documents)