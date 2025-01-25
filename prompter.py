# prompter.py
from constants import AI_NAME, AI_MODE, SYSTEM_PROMPT
from state import State
from memory import MemoryManager

class Prompter:
    def build_prompt(
        state: State,
        memory_manager: MemoryManager,
        user_message: str
    ) -> str:
        """
        Builds a multi-part prompt, instructing the model to produce JSON with:
          - wantsToSpeak (bool)
          - reply (string)
          - internalMonologue (string)
        Also includes the AI's mode (conversation or discussion).
        """
        # 1) Format the system prompt with AI_NAME and AI_MODE
        system_prompt = SYSTEM_PROMPT.format(AI_NAME=AI_NAME, AI_MODE=AI_MODE).strip()

        # 2) Retrieve top relevant memories
        relevant_memories = memory_manager.get_relevant_memories(user_message)
        memory_texts = "\n".join([m["document"] for m in relevant_memories])

        # 3) Gather up to last few lines of short-term context
        recent_context_lines = state.short_term[-5:]
        recent_context_text = "\n".join(recent_context_lines)

        # 4) Combine them into a single final prompt
        final_prompt = f"""{system_prompt}

        Relevant Memories:
        {memory_texts}

        Recent Conversation:
        {recent_context_text}

        User's new message:
        {user_message}

        Respond in JSON.
        Produce a single JSON object with keys: 'wantsToSpeak', 'reply', 'internalMonologue'.
        No extra text outside JSON.
        """

        return final_prompt