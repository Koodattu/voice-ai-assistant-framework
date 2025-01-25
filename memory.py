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
    A simpler MemoryManager that:
      - Saves each user message in the DB.
      - Every N new user messages, generates a very short summary of those last messages.
      - Uses a simple retrieval method that sorts by embedding distance only.
      - Runs in its own thread (so it doesn't block the orchestrator).
    """

    def __init__(self, state: State):
        """
        :param state: Shared application state.
        """
        self.state = state

        # Keep track of how many user messages we've already saved/summarized.
        self.last_saved_count = 0

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(name="memory_collection")
        logger.info(f"MemoryManager: Loaded {self.collection.count()} memories from database.")

    def run(self):
        """
        A simple event loop that checks for new user messages every second and:
          1. Saves each new user message to the DB.
          2. Every N messages, generates a short summary and saves it as a separate memory.
        """
        logger.info("MemoryManager: Starting memory thread (run).")
        while not self.state.shutdown:
            self.handle_new_messages()
            time.sleep(1)  # Sleep for a second so we don't hammer the CPU

    def handle_new_messages(self):
        """
        Check how many user messages we have (user_message_count) vs. how many we've saved.
        Save any new user messages. If we've hit a multiple of summary_interval, do a short summary.
        """
        current_count = self.state.user_message_count
        if current_count > self.last_saved_count:
            # Save all new user messages
            self.save_new_user_messages(self.last_saved_count, current_count)

            # If we've hit a multiple of 'MEMORY_INTERVAL', generate a short summary
            if current_count % MEMORY_INTERVAL == 0:
                self.generate_short_summary()

            self.last_saved_count = current_count

    def save_new_user_messages(self, start_idx: int, end_idx: int):
        """
        Saves each user message from short_term that has not been saved yet.
        We rely on the naming format in short_term: 'User: <message>'.
        """
        logger.debug(f"MemoryManager: Saving user messages from index={start_idx} to {end_idx - 1}.")
        # short_term may contain both user and AI lines; we only want user lines.
        # However, the simplest approach is to pick out lines from short_term
        # that correspond to the user message indices we haven't saved yet.
        # For instance, if the user_message_count is 12, that means we have 12 user lines,
        # but short_term also includes AI lines. We'll collect only the newly added user lines.
        user_lines_collected = 0
        for line in reversed(self.state.short_term):
            if line.startswith("User: "):
                user_lines_collected += 1
                if user_lines_collected <= (end_idx - start_idx):
                    # This is one of the new user messages
                    msg_text = line[len("User: "):].strip()
                    self.add_memory(msg_text, metadata={"type": "raw-user-msg", "importance": 1.0})
                else:
                    break

    def generate_short_summary(self):
        """
        Generate a very short memory summarizing the last 'count' user messages.
        Then store it with a slightly higher importance. Example prompt included below.
        """
        logger.info(f"MemoryManager: Generating a short summary for the last {MEMORY_INTERVAL} user messages.")
        # Gather the last 'count' user messages from short_term
        user_lines = []
        for line in reversed(self.state.short_term):
            if line.startswith("User: "):
                user_lines.append(line[len("User: "):].strip())
                if len(user_lines) == MEMORY_INTERVAL:
                    break
        user_lines.reverse()
        conversation_text = "\n".join(user_lines)

        # Build prompt
        prompt = (
            f"Given these {MEMORY_INTERVAL} user messages:\n"
            f"---\n{conversation_text}\n---\n"
            f"Write a concise memory (1-2 short sentences) capturing the key ideas."
        )

        # Use the LLM to summarize
        short_summary = LLMModule.generate_response(prompt)

        logger.debug(f"MemoryManager: Short summary content: {short_summary}")
        self.add_memory(short_summary, metadata={"type": "short-summary", "importance": 2.0})

    def add_memory(self, content: str, metadata: dict = None):
        """
        Adds a new memory to the ChromaDB. No recency or decay logic—just store it.
        """
        if metadata is None:
            metadata = {}
        memory_id = str(uuid.uuid4())
        self.collection.upsert(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata]
        )
        logger.debug(f"MemoryManager: Added memory ID={memory_id} type={metadata.get('type')} importance={metadata.get('importance')}")

    def get_relevant_memories(self, query: str) -> List[dict]:
        """
        Retrieves up to MEMORY_RECALL_COUNT memories by distance-only. No recency or decay.
        """
        if not query.strip():
            return []
        try:
            result = self.collection.query(query_texts=[query], n_results=MEMORY_RECALL_COUNT)
            memories = []
            for i, mem_id in enumerate(result["ids"][0]):
                memories.append({
                    "id": mem_id,
                    "document": result["documents"][0][i],
                    "metadata": result["metadatas"][0][i],
                    "distance": result["distances"][0][i],
                })
            # Sort ascending by distance (lower = more similar)
            memories.sort(key=lambda x: x["distance"])
            # Return as many as we can
            return memories[:MEMORY_RECALL_COUNT]
        except Exception as e:
            logger.error(f"MemoryManager: Error retrieving relevant memories: {e}")
            return []