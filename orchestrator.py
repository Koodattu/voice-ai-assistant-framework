import time
from state import State
from constants import PATIENCE_SECONDS
from llm import LLMModule
from tts import TTSModule
from memory import MemoryManager
from logger import logger

class Orchestrator:
    def __init__(self, state: State, llm_module: LLMModule, tts_module: TTSModule, memory_manager: MemoryManager):
        logger.info("Orchestrator: Initializing orchestrator module.")
        self.state = state
        self.llm_module = llm_module
        self.tts_module = tts_module
        self.memory_manager = memory_manager

    def run(self):
        """Continuously decide when to prompt the LLM."""
        logger.info("Orchestrator: Starting orchestrator module.")
        while not self.state.shutdown:
            # Check if there are new user messages and that no one is busy.
            user_busy = self.state.user_talking
            ai_busy = self.state.ai_talking or self.state.ai_thinking
            messages_available = len(self.state.new_messages) > 0

            if messages_available and (not user_busy) and (not ai_busy):
                # Consolidate all pending new messages into a single block.
                user_messages = self.state.new_messages.copy()
                self.state.new_messages.clear()
                consolidated_message = " ".join(user_messages)
                logger.info(f"Orchestrator: Consolidated user message: {consolidated_message}")

                # Proceed to prompt the LLM.
                self.prompt_llm(consolidated_message)

            # Silence scenario: if no new messages and timeout passed
            elif (time.time() - self.state.last_message_timestamp) > PATIENCE_SECONDS:
                logger.info("Orchestrator: Silence detected - prompting LLM using recent conversation context.")
                silent_message = "..."  
                # Add a placeholder to short-term memory to record the silence period.
                self.state.add_new_message(silent_message)

                # In the silence scenario, use the most recent conversation context as the prompt.
                self.prompt_llm(silent_message)

            time.sleep(0.1)

    def prompt_llm(self, last_user_message: str):
        """
        Build the LLM prompt by combining relevant memories, 
        short-term conversation context, and the latest user input,
        then query the LLM and handle the AI's response.
        """
        if self.state.user_talking or self.state.ai_talking or self.state.ai_thinking:
            logger.info("Orchestrator: Detected that the AI or user is busy; skipping prompt.")
            return

        # Build the final prompt using MemoryManager
        final_prompt = self.memory_manager.build_prompt_for_llm(last_user_message)
        logger.debug(f"Orchestrator: Final prompt for LLM:\n{final_prompt}")

        # Query the LLM
        ai_response = self.llm_module.generate_response(final_prompt)
        logger.info("Orchestrator: Received AI response.")

        # Add to short-term memory
        self.state.short_term.append(f"AI: {ai_response}")
        if len(self.state.short_term) > 10:
            removed = self.state.short_term.pop(0)
            logger.debug(f"Orchestrator: Removed oldest short-term memory: {removed}")

        # Send response to TTS
        self.tts_module.speak(ai_response)
        logger.info("Orchestrator: AI response sent to TTS module.")