# memory.py
import uuid
import asyncio
import time
from typing import List
import chromadb
from chromadb.config import Settings
import requests
from constants import (
    MEMORY_RECALL_COUNT,
    CHROMA_PERSIST_DIRECTORY,
    LLM_API_URL,
    LLM_MODEL,
    REFLECTION_IMPORTANCE_THRESHOLD,
    RECENCY_DECAY_FACTOR,
    IMPORTANCE_WEIGHT,
    RECENCY_WEIGHT,
    RELEVANCE_WEIGHT,
    MAX_RETRIEVAL_RESULTS
)
from state import State
from logger import logger
import math

class MemoryManager:
    def __init__(self, state: State):
        """
        MemoryManager handles short-term, long-term, and reflection memories using ChromaDB.
        """
        self.state = state
        self.processed_count = 0

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(name="memory_collection")
        logger.info(f"MemoryManager: Loaded {self.collection.count()} memories from database.")

    def add_memory(self, content: str, metadata: dict = None):
        """
        Adds a new memory to ChromaDB with timestamps (creation_time, last_accessed).
        Optionally includes an 'importance' value.
        """
        if metadata is None:
            metadata = {}
        metadata.setdefault("type", "short-term")
        metadata.setdefault("importance", 1.0)  # Default importance
        now = time.time()
        metadata["creation_time"] = now
        metadata["last_accessed"] = now

        memory_id = str(uuid.uuid4())
        self.collection.upsert(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata]
        )
        logger.debug(f"MemoryManager: Added memory ID {memory_id} with type={metadata['type']} importance={metadata['importance']}")

    def get_memory_by_id(self, memory_id: str):
        """
        Retrieve a single memory by ID. Returns None if not found.
        """
        try:
            result = self.collection.get(ids=[memory_id])
            if not result["ids"]:
                return None
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0],
            }
        except Exception as e:
            logger.error(f"MemoryManager: Error getting memory by ID {memory_id}: {e}")
            return None

    def update_memory_access_time(self, memory_id: str):
        """
        Update the last_accessed timestamp for a specific memory.
        """
        mem = self.get_memory_by_id(memory_id)
        if mem:
            mem["metadata"]["last_accessed"] = time.time()
            self.collection.upsert(
                ids=[memory_id],
                documents=[mem["document"]],
                metadatas=[mem["metadata"]]
            )

    def get_memories(self, query: str = "") -> List[dict]:
        """
        Retrieves memories from the database without custom scoring.
        If query is blank, returns all memories. Primarily for debugging.
        """
        data = []
        if not query:
            # Fetch all
            memories = self.collection.get()
            for i in range(len(memories["ids"])):
                data.append({
                    "id": memories["ids"][i],
                    "document": memories["documents"][i],
                    "metadata": memories["metadatas"][i]
                })
            logger.debug(f"MemoryManager: Retrieved {len(data)} total memories (no query).")
        else:
            # Basic embedding-based retrieval
            memories = self.collection.query(query_texts=[query], n_results=MEMORY_RECALL_COUNT)
            for i in range(len(memories["ids"][0])):
                data.append({
                    "id": memories["ids"][0][i],
                    "document": memories["documents"][0][i],
                    "metadata": memories["metadatas"][0][i],
                    "distance": memories["distances"][0][i]
                })
            logger.debug(f"MemoryManager: Retrieved {len(data)} relevant memories for query='{query}'.")
        return data

    def get_relevant_memories(self, query: str) -> List[dict]:
        """
        Retrieve the top memories relevant to the query by combining:
        - Relevance (1 - distance from embedding search)
        - Recency (exponential decay from last_accessed)
        - Importance (metadata['importance'])

        Returns up to MEMORY_RECALL_COUNT of the highest-scoring memories.
        """
        if not query.strip():
            logger.debug("MemoryManager: Empty query; returning no relevant memories.")
            return []

        # Retrieve more results than we need, then custom-score them
        raw_results = self.collection.query(query_texts=[query], n_results=MAX_RETRIEVAL_RESULTS)
        results = []
        now = time.time()

        for i, mem_id in enumerate(raw_results["ids"][0]):
            # Basic fields
            doc = raw_results["documents"][0][i]
            meta = raw_results["metadatas"][0][i]
            dist = raw_results["distances"][0][i]  # smaller = more relevant
            # Safety checks
            creation_time = meta.get("creation_time", now)
            last_accessed = meta.get("last_accessed", now)
            importance = float(meta.get("importance", 1.0))

            # Compute recency factor
            # You can use creation_time or last_accessed, or combine both
            age = now - last_accessed  # seconds since last accessed
            recency_factor = math.exp(-RECENCY_DECAY_FACTOR * age)

            # Relevance is 1 - distance
            relevance_score = 1 - dist

            # Weighted sum
            score = (
                (RELEVANCE_WEIGHT * relevance_score) +
                (RECENCY_WEIGHT * recency_factor) +
                (IMPORTANCE_WEIGHT * importance)
            )

            results.append({
                "id": mem_id,
                "document": doc,
                "metadata": meta,
                "distance": dist,
                "score": score
            })

        # Sort by descending final score
        results.sort(key=lambda x: x["score"], reverse=True)

        # Update last_accessed for top results
        top_results = results[:MEMORY_RECALL_COUNT]
        for mem in top_results:
            self.update_memory_access_time(mem["id"])

        logger.debug(f"MemoryManager: Retrieved {len(top_results)} top-scored memories for query='{query}'.")
        return top_results

    def summarize_memories(self):
        """
        Summarizes recent short-term conversation and stores it as a long-term memory.
        (You could also incorporate advanced reflection logic here or keep it separate.)
        """
        if self.state.user_message_count % 10 != 0 or self.state.user_message_count <= 0:
            logger.debug("MemoryManager: Not time to summarize yet.")
            return  # Summarize every 10 user messages

        logger.info("MemoryManager: Generating summary of recent conversations.")
        conversation_text = "\n".join(self.state.short_term)
        prompt = (
            f"Summarize the following conversation into key points or Q&A pairs:\n"
            f"---\n{conversation_text}\n---\n"
            f"Return the most important facts or topics that should be remembered."
        )

        summary = self.generate_summary(prompt)
        logger.debug(f"MemoryManager: Summary generated: {summary[:60]}...")

        # Store the summary as a long-term memory with higher importance
        self.add_memory(summary, metadata={"type": "long-term", "importance": 3.0})
        logger.info("MemoryManager: Summary stored as a long-term memory.")

    def perform_reflection(self):
        """
        Periodically generate higher-level reflections if recent memories have a high total importance.
        The reflection is then stored as a new memory with references to the parent memories.
        """
        # Gather recent short-term or important memories
        # For simplicity, let's say the last 20 short-term or important ones
        all_memories = self.get_memories()  # Or a narrower query based on recency
        # Filter those from the last hour, for example
        now = time.time()
        recent = []
        total_importance = 0.0
        for mem in all_memories:
            meta = mem["metadata"]
            if (now - meta.get("creation_time", now)) < 3600:  # last hour
                recent.append(mem)
                total_importance += meta.get("importance", 1.0)

        # If the total importance is above threshold, generate reflection
        if total_importance >= REFLECTION_IMPORTANCE_THRESHOLD and len(recent) > 0:
            logger.info("MemoryManager: Reflection triggered by high-importance recent memories.")
            # Build reflection prompt
            recent_text = "\n".join([m["document"] for m in recent])
            prompt = (
                f"Review the following important memories:\n\n{recent_text}\n\n"
                f"Generate a higher-level reflection or insight that summarizes patterns or lessons."
            )
            reflection_text = self.generate_summary(prompt)
            # Store reflection as a new memory with references to the parents
            parent_ids = [m["id"] for m in recent]
            meta = {
                "type": "reflection",
                "parents": parent_ids,
                "importance": 10.0  # reflections often have high importance
            }
            self.add_memory(reflection_text, meta)
            logger.info("MemoryManager: Reflection stored as a new 'reflection' memory.")

    def generate_summary(self, prompt: str) -> str:
        """
        Sends a prompt to the LLM to generate a summary or reflection.
        """
        try:
            payload = {
                "prompt": prompt,
                "model": LLM_MODEL,
                "stream": False
            }
            logger.info("MemoryManager: Sending summarization/reflection prompt to LLM.")
            logger.debug(f"MemoryManager: Summarization payload: {payload}")
            response = requests.post(LLM_API_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            summary = data.get("response", "")
            logger.debug("MemoryManager: Received summary from LLM.")
            return summary
        except requests.exceptions.RequestException as e:
            logger.error(f"MemoryManager: Error communicating with LLM API: {e}")
            return "(Error generating summary)"
        except KeyError:
            logger.error("MemoryManager: Unexpected response format from LLM API.")
            return "(Error generating summary)"

    def build_prompt_for_llm(self, user_message: str) -> str:
        """
        Builds the final prompt for the LLM by combining:
        - top-scored relevant memories
        - short-term conversation
        - the latest user message
        """
        relevant_memories = self.get_relevant_memories(user_message)
        memories_text = "\n".join([m["document"] for m in relevant_memories])
        short_term_messages = self.state.short_term[:-1] if len(self.state.short_term) > 1 else []
        short_term_text = "\n".join(short_term_messages)

        final_prompt = f"""
You are a helpful assistant. Below are relevant facts from memory:
{memories_text}

Here is the recent conversation:
{short_term_text}

Now the user says:
User: {user_message}

Please respond in a clear and concise manner, considering past context. Keep the answer short consisting of one or two sentence(s).
"""
        logger.debug("MemoryManager: Built final prompt for LLM.")
        return final_prompt

    async def periodic_tasks(self, interval: int = 60):
        """
        Periodically checks and summarizes memories, then checks for reflection triggers.
        """
        while not self.state.shutdown:
            self.summarize_memories()
            self.perform_reflection()
            self.prune_memories()
            await asyncio.sleep(interval)

    def prune_memories(self):
        """
        Prunes outdated or low-importance memories.
        This is a simple example; in production, you might have more robust logic.
        """
        try:
            all_memories = self.get_memories()
            to_remove = []
            now = time.time()
            for mem in all_memories:
                meta = mem["metadata"]
                age = now - meta.get("creation_time", now)
                importance = meta.get("importance", 1.0)
                # Example rule: if memory is older than 24h and importance < 2, remove it
                if age > 86400 and importance < 2:
                    to_remove.append(mem["id"])

            if to_remove:
                self.collection.delete(ids=to_remove)
                logger.info(f"MemoryManager: Pruned {len(to_remove)} old, low-importance memories.")
        except Exception as e:
            logger.error(f"MemoryManager: Failed to prune memories: {e}")

    def run(self):
        """
        Entry point for the memory module. Starts periodic summarization/reflection tasks.
        """
        logger.info("MemoryManager: Running periodic summarization and reflection tasks.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.periodic_tasks())
        finally:
            loop.close()
            logger.info("MemoryManager: Event loop closed.")
