# memory.py
import uuid
import time
from typing import List
import chromadb
from chromadb.config import Settings
from constants import (
    MEMORY_RECALL_COUNT,
    CHROMA_PERSIST_DIRECTORY,
    MEMORY_INTERVAL
)
from llm import LLMModule
from state import State
from logger import logger


class MemoryManager:
    """
    MemoryManager saves and summarizes conversations intelligently:
      - Summaries are generated every MEMORY_INTERVAL messages.
      - Only summaries (not individual messages) are saved to persistent storage.
    """

    def __init__(self, state: State):
        self.state = state
        self.last_saved_count = 0
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(name="memory_collection")
        logger.info(f"MemoryManager: Loaded {self.collection.count()} memories from database.")

    def run(self):
        """
        Periodically process new messages and summarize interactions.
        """
        logger.info("MemoryManager: Starting memory thread.")
        while not self.state.shutdown:
            self.process_new_messages()
            time.sleep(0.1)  # Check every second to reduce CPU usage

    def process_new_messages(self):
        """
        Check for new user messages and generate summaries if needed.
        """
        current_count = self.state.user_message_count
        if current_count > self.last_saved_count:
            # Check if it's time to summarize
            if current_count % MEMORY_INTERVAL == 0:
                self.generate_summary()
            self.last_saved_count = current_count

    def generate_summary(self):
        """
        Generates a summary for the last MEMORY_INTERVAL user messages and saves it.
        """
        logger.info("MemoryManager: Generating a concise summary.")
        user_lines = [
            line[len("User: "):].strip()
            for line in reversed(self.state.short_term)
            if line.startswith("User: ")
        ][:MEMORY_INTERVAL]
        user_lines.reverse()

        if not user_lines:
            logger.debug("MemoryManager: No user lines found to summarize.")
            return

        conversation_text = "\n".join(user_lines)

        # Prompt for summary generation
        prompt = (
            f"Summarize the following {MEMORY_INTERVAL} user messages into 1-2 sentences:\n"
            f"---\n{conversation_text}\n---\n"
            f"Keep it concise and capture key ideas."
        )
        summary = LLMModule.generate_response(prompt)
        logger.debug(f"MemoryManager: Generated summary: {summary}")

        # Save the summary with higher importance
        self.add_memory(summary, metadata={"type": "summary", "importance": 2.0})

    def add_memory(self, content: str, metadata: dict):
        """
        Saves summaries (and only summaries) to persistent storage.
        """
        if not content.strip():
            logger.debug("MemoryManager: Empty content, not saving.")
            return

        memory_id = str(uuid.uuid4())
        self.collection.upsert(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata]
        )
        logger.info(f"MemoryManager: Saved memory ID={memory_id} with type={metadata.get('type')}.")

    def get_relevant_memories(self, query: str) -> List[dict]:
        """
        Retrieves relevant summaries for the given query.
        """
        if not query.strip():
            return []
        try:
            result = self.collection.query(query_texts=[query], n_results=MEMORY_RECALL_COUNT)
            memories = [
                {
                    "id": result["ids"][0][i],
                    "document": result["documents"][0][i],
                    "metadata": result["metadatas"][0][i],
                    "distance": result["distances"][0][i],
                }
                for i in range(len(result["ids"][0]))
            ]
            return sorted(memories, key=lambda x: x["distance"])[:MEMORY_RECALL_COUNT]
        except Exception as e:
            logger.error(f"MemoryManager: Retrieval error: {e}")
            return []