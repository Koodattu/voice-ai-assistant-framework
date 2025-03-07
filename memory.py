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
    MemoryManager saves and summarizes conversations.
    Memories are tagged with the current call's GUID.
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
        logger.info("MemoryManager: Starting memory thread.")
        while not self.state.shutdown:
            self.process_new_messages()
            time.sleep(0.1)

    def process_new_messages(self):
        # Only process if in a call
        if not self.state.in_call:
            return

        current_count = self.state.user_message_count
        if current_count > self.last_saved_count:
            if current_count % MEMORY_INTERVAL == 0:
                self.generate_summary()
            self.last_saved_count = current_count

    def generate_summary(self):
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
        prompt = (
            f"Summarize the following {MEMORY_INTERVAL} user messages into 1-2 sentences:\n"
            f"---\n{conversation_text}\n---\n"
            f"Keep it concise and capture key ideas."
        )
        summary = LLMModule.generate_response(prompt)
        logger.debug(f"MemoryManager: Generated summary: {summary}")
        self.add_memory(summary, metadata={"type": "summary", "importance": 2.0})

    def add_memory(self, content: str, metadata: dict):
        if not content.strip():
            logger.debug("MemoryManager: Empty content, not saving.")
            return

        # If there's a current call ID, tag the memory with it.
        if self.state.current_call_id:
            metadata["call_id"] = self.state.current_call_id

        memory_id = str(uuid.uuid4())
        self.collection.upsert(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata]
        )
        logger.info(f"MemoryManager: Saved memory ID={memory_id} with metadata={metadata}.")

    def get_relevant_memories(self, query: str) -> List[dict]:
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
