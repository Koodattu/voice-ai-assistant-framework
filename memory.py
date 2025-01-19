# memory.py

import time
from typing import List

# You'd import Chroma, or whichever vector store you use.
# For example:
# from chromadb.config import Settings
# import chromadb

# from llm import LLMModule  # If memory needs to call the LLM to do summarization

class MemoryManager:
    def __init__(self, short_term_limit=10):
        """
        short_term_limit: how many recent messages (user+AI) we keep in short-term memory.
        """
        # Short-term memory: just a Python list of strings, e.g. ["User: Hello", "AI: Hi", ...]
        self.short_term = []
        self.short_term_limit = short_term_limit

        # Example: create or connect to a Chroma database
        # self.chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="db"))
        # self.collection = self.chroma_client.get_or_create_collection(name="memory_collection")

        # Just placeholders here
        self.chroma_client = None
        self.collection = None

        # Count how many user messages have arrived, to know when to summarize
        self.user_message_count = 0

    def add_to_short_term(self, role: str, content: str):
        """
        Add a new line (User or AI) to short-term memory. 
        If we exceed the short_term_limit, we remove the oldest line(s).
        """
        self.short_term.append(f"{role}: {content}")
        # If we exceed short_term_limit *total lines*, remove from the front.
        while len(self.short_term) > self.short_term_limit:
            self.short_term.pop(0)

        # If it's a user message, increment user_message_count
        if role.lower() == "user":
            self.user_message_count += 1

    def get_short_term_context(self) -> List[str]:
        """Return the last N lines of conversation as a list of strings."""
        return self.short_term

    def maybe_summarize_short_term(self, llm_module):
        """
        If we've hit a multiple of (say) 10 user messages, 
        generate a summary or Q&A pairs from short_term 
        and store them in Chroma DB as a new 'memory chunk'.
        """
        # For example, every 10 user messages, we run summarization
        if self.user_message_count % 10 == 0 and self.user_message_count > 0:
            print("[Memory] Summarizing short-term memory...")

            # 1) Build a summarization prompt using short_term
            conversation_text = "\n".join(self.short_term)
            prompt = f"""Summarize the following conversation into key points or Q&A pairs:
            ---
            {conversation_text}
            ---
            Return the most important facts or topics that should be remembered."""

            # 2) Call the LLM to get a summary
            summary = llm_module.generate_response_for_memory(prompt)
            print("[Memory] Summarization result:", summary)

            # 3) Store summary in the vector DB
            self.store_long_term_memory(summary)

    def store_long_term_memory(self, summary: str):
        """
        Store the summary in Chroma DB with an embedding.
        For real usage, you'd do something like:
        
        embedding = embed(summary)  # get your embedding from some function
        self.collection.add(documents=[summary], embeddings=[embedding], metadatas=[...])
        """
        print(f"[Memory] Storing summary in long-term DB: {summary[:60]}...")
        # Placeholder: do real DB insertion

    def get_relevant_memories(self, query: str) -> List[str]:
        """
        Query the vector DB for relevant memories to the given user query.
        For real usage, you'd do something like:

        query_embedding = embed(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        return [doc for doc in results["documents"][0]]
        """
        print(f"[Memory] Searching for relevant memories for: {query}")
        # Return a placeholder or empty for now
        return []

    def build_llm_prompt(self, user_message: str, relevant_memories: List[str]) -> str:
        """
        Build the final prompt for the LLM using:
         1) relevant long-term memories
         2) the short-term conversation
         3) the new user message
        or any other instructions you want to provide.

        Typically, you'd create something like a system prompt:
        e.g. "You are ChatGPT. You have the following relevant knowledge: {relevant_memories}...
        Then you have the short-term conversation, then the new user message."
        """
        memories_text = "\n".join(relevant_memories)
        short_term_text = "\n".join(self.short_term)

        # Example structure:
        final_prompt = f"""
You are a helpful assistant. Below are relevant facts from memory:
{memories_text}

Here is the recent conversation:
{short_term_text}

Now the user says:
User: {user_message}

Please respond in a clear and concise manner.
"""
        return final_prompt
