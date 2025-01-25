# prompter.py
from constants import AI_NAME, SYSTEM_PROMPT, MEMORY_RECALL_COUNT
from state import State
from memory import MemoryManager

class Prompter:
    def build_prompt(
        state: State,
        memory_manager: MemoryManager,
        user_message: str
    ) -> str:
        """
        Builds a multi-part prompt:
          1. System prompt (defines AI identity and instructions).
          2. Relevant memories from DB, sorted by embedding distance (or other logic).
          3. Recent conversation context from short-term memory.
          4. The new user message.

        Returns the final combined prompt for the LLM.
        """

        # 1) Format the system prompt with AI_NAME
        system_prompt = SYSTEM_PROMPT.format(AI_NAME=AI_NAME).strip()

        # 2) Retrieve top relevant memories (distance-based in this example)
        relevant_memories = memory_manager.get_relevant_memories(user_message)
        memory_texts = "\n".join([m["document"] for m in relevant_memories])

        # 3) Gather up to the last few lines of short-term context
        recent_context_lines = state.short_term[-5:]  # last 5 lines total
        recent_context_text = "\n".join(recent_context_lines)

        # 4) Combine them into a single final prompt
        #    You can adopt an OpenAI style by prefixing with a system message, then user message, etc.
        #    But for your local LLM, the actual format might differ. Here’s one example:
        final_prompt = f"""{system_prompt}

Relevant Memories:
{memory_texts}

Recent Conversation:
{recent_context_text}

The user just said:
User: {user_message}

Reply in a concise manner as {AI_NAME}:
"""
        return final_prompt