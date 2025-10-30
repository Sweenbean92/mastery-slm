import chromadb
import shutil

def delete_chroma_database(db_path="./chroma_db"):
    try:
        # First, try to close any existing client connections
        #client = chromadb.PersistentClient(path=db_path)
        #client.reset()
        
        # Delete the database directory
        shutil.rmtree(db_path)
        print(f"Successfully deleted ChromaDB database at {db_path}")
    except Exception as e:
        print(f"Error deleting database: {str(e)}")

if __name__ == "__main__":
    # You can specify a different path if needed
    delete_chroma_database()