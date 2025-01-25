import time
from state import State
from constants import AI_MODE, AI_NAME, AI_MODE_CONVERSATION, AI_MODE_DISCUSSION, SILENCE_THRESHOLD
from llm import LLMModule
from tts import TTSModule
from memory import MemoryManager
from logger import logger
from prompter import Prompter

class Orchestrator:
    def __init__(self, state: State, tts_module: TTSModule, memory_manager: MemoryManager):
        logger.info("Orchestrator: Initializing orchestrator module.")
        self.state = state
        self.tts_module = tts_module
        self.memory_manager = memory_manager

    def run(self):
        logger.info("Orchestrator: Starting orchestrator module.")
        while not self.state.shutdown:
            # Define state flags
            system_ready = self.state.system_ready
            user_busy = self.state.user_talking
            ai_busy = self.state.ai_talking or self.state.ai_thinking
            messages_available = len(self.state.new_messages) > 0
            silence_elapsed = (time.time() - self.state.last_message_timestamp) > SILENCE_THRESHOLD

            # Consolidate conditions for action
            if not user_busy and not ai_busy and system_ready:
                if messages_available:  # New user messages available
                    self.handle_new_user_messages()
                elif silence_elapsed:
                    # Silence threshold logic (applies to both modes)
                    logger.info("Orchestrator: Silence threshold reached, generating response.")
                    self.state.last_message_timestamp = time.time()
                    self.prompt_llm("... (long silence)")

            time.sleep(0.1)

    def handle_new_user_messages(self):
        user_messages = self.state.new_messages.copy()
        self.state.new_messages.clear()
        consolidated_message = " ".join(user_messages)
        logger.info(f"Orchestrator: Consolidated user message: {consolidated_message}")
        self.prompt_llm(consolidated_message)

    def prompt_llm(self, last_user_message: str):
        if self.state.user_talking or self.state.ai_talking or self.state.ai_thinking:
            logger.info("Orchestrator: AI or user is busy; skipping prompt.")
            return

        self.state.ai_thinking = True
        # Build prompt
        prompt = Prompter.build_prompt(self.state, self.memory_manager, last_user_message)
        # LLM call
        response_dict = LLMModule.generate_json_response(prompt)

        # Parse response JSON
        wants_to_speak = response_dict.get("wantsToSpeak", False)
        reply_text = response_dict.get("reply", "")
        internal_monologue = response_dict.get("internalMonologue", "")

        logger.info("Orchestrator: AI JSON response: " + str(response_dict))

        # (Optional) Store the internal monologue in memory or a “notebook”
        # e.g.:
        # self.memory_manager.add_memory(internal_monologue, {"type": "monologue", "importance": 1.0})

        # If AI wants to speak, we speak
        if wants_to_speak and reply_text.strip():
            self.state.short_term.append(f"AI: {reply_text}")
            if len(self.state.short_term) > 10:
                removed = self.state.short_term.pop(0)
                logger.debug(f"Orchestrator: Removed oldest short-term memory: {removed}")
            self.tts_module.speak(reply_text)
            logger.info("Orchestrator: AI response spoken.")
        else:
            logger.info("Orchestrator: AI does not wish to speak.")

        self.state.ai_thinking = False