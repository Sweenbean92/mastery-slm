import chromadb

# Initialize ChromaDB client
client = chromadb.Client()

collection = client.get_or_create_collection(name="documents")
collection.delete(ids="all")  # Delete all documents in the collection