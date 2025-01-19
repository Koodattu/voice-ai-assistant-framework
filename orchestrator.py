# orchestrator.py

import time
from state import State
from constants import PATIENCE_SECONDS
from llm import LLMModule
from tts import TTSModule
from memory import MemoryManager

class Orchestrator:
    def __init__(self, state: State, llm_module: LLMModule, tts_module: TTSModule):
        self.state = state
        self.llm_module = llm_module
        self.tts_module = tts_module
        self.memory = MemoryManager(short_term_limit=10)

    def run(self):
        """Continuously decide when to prompt the LLM."""
        print("[Orchestrator] Starting orchestrator module.")
        while True:
            with self.state.lock:
                if self.state.shutdown:
                    print("[Orchestrator] Shutting down orchestrator.")
                    break

            # Check if there are new user messages and that no one is busy.
            with self.state.lock:
                user_busy = self.state.user_talking
                ai_busy = self.state.ai_talking or self.state.ai_thinking
                messages_available = len(self.state.new_messages) > 0

            if messages_available and (not user_busy) and (not ai_busy):
                # Consolidate all pending new messages into a single block.
                user_messages = []
                with self.state.lock:
                    while self.state.new_messages:
                        user_messages.append(self.state.new_messages.pop(0))
                consolidated_message = " ".join(user_messages)
                print(f"[Orchestrator] Consolidated user message: {consolidated_message}")

                # Add the consolidated user message to short-term memory.
                self.memory.add_to_short_term("User", consolidated_message)
                # Optionally, trigger summarization if needed.
                self.memory.maybe_summarize_short_term(self.llm_module)

                # Proceed to prompt the LLM.
                self.prompt_llm(consolidated_message)

            # Silence scenario: if there are no new messages and a certain timeout has passed,
            # prompt the LLM to continue the conversation by generating a probing response.
            elif (time.time() - self.state.last_message_timestamp) > PATIENCE_SECONDS:
                print("[Orchestrator] Silence detected - prompting LLM using recent conversation context.")
                # Here we do not have a new user message, but we still want a response.
                silent_message = "..."  
                # Add a placeholder to short-term memory to record the silence period.
                self.memory.add_to_short_term("User", silent_message)
                # As before, check if summarization is needed.
                self.memory.maybe_summarize_short_term(self.llm_module)

                # In the silence scenario, use the most recent conversation context as the prompt.
                self.prompt_llm(silent_message)

            time.sleep(0.1)

    def prompt_llm(self, last_user_message: str):
        """
        Build the LLM prompt by combining relevant long-term memories, 
        the short-term conversation context, and the latest (possibly consolidated) user input,
        then query the LLM and handle the AI's response.
        """
        with self.state.lock:
            # Recheck that neither user nor AI is busy.
            if self.state.user_talking or self.state.ai_talking or self.state.ai_thinking:
                print("[Orchestrator] Detected that the AI or user is busy; skipping prompt.")
                return

        # Retrieve relevant long-term memories for context.
        relevant_memories = self.memory.get_relevant_memories(last_user_message)

        # Build the final prompt that injects the retrieved memories and the short-term conversation.
        final_prompt = self.memory.build_llm_prompt(last_user_message, relevant_memories)
        print("[Orchestrator] Final prompt for LLM:\n", final_prompt)

        # Query the LLM for a response using the built prompt.
        ai_response = self.llm_module.generate_response(final_prompt)
        print("[Orchestrator] LLM response:", ai_response)

        # Add the AI's response to short-term memory.
        self.memory.add_to_short_term("AI", ai_response)
        # Pass the AI response to TTS to be spoken.
        self.tts_module.speak(ai_response)
