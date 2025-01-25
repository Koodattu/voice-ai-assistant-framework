import sys
sys.path.append("..")
import chromadb
from chromadb.config import Settings

# Configure the ChromaDB client
CHROMA_PERSIST_DIRECTORY = "./chromadb"  # Adjust this path to your database directory
OUTPUT_FILE = "chroma_memories.txt"  # Output file for storing memories

def fetch_and_save_memories():
    # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIRECTORY,
        settings=Settings(anonymized_telemetry=False)
    )

    # Retrieve the memory collection
    collection = chroma_client.get_or_create_collection(name="memory_collection")
    memories = collection.get()  # Fetch all memories

    # Write memories to a text file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write("Stored Memories in ChromaDB:\n\n")
        for i in range(len(memories["ids"])):
            memory_id = memories["ids"][i]
            document = memories["documents"][i]
            metadata = memories["metadatas"][i]

            file.write(f"Memory ID: {memory_id}\n")
            file.write(f"Document: {document}\n")
            file.write(f"Metadata: {metadata}\n")
            file.write("-" * 50 + "\n")

    print(f"Memories have been saved to {OUTPUT_FILE}")

# Run the script
if __name__ == "__main__":
    fetch_and_save_memories()
