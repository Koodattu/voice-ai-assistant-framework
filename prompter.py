from config import AI_NAME, AI_MODE, SYSTEM_PROMPT
from state import State

class Prompter:
    def build_prompt(
        state: State,
        user_message: str
    ) -> str:
        """
        Builds a multi-part prompt, instructing the model to produce JSON with:
          - wantsToSpeak (bool)
          - reply (string)
          - internalMonologue (string)
        Also includes the AI's mode (conversation or discussion).
        """
        # Format the system prompt with AI_NAME and AI_MODE
        system_prompt = SYSTEM_PROMPT.format(AI_NAME=AI_NAME, AI_MODE=AI_MODE).strip()

        # Gather up to last few lines of short-term context
        recent_context_lines = state.short_term[-5:]
        recent_context_text = "\n".join(recent_context_lines)

        # Combine them into a single final prompt
        final_prompt = f"""{system_prompt}

        Recent Conversation:
        {recent_context_text}

        User's new message:
        {user_message}

        Respond in JSON.
        Produce a single JSON object with keys: 'wantsToSpeak', 'reply', 'internalMonologue'.
        No extra text outside JSON.
        """

        return final_prompt