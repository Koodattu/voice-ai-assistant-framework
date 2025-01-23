# llm.py (example changes)

import requests
import traceback
from state import State
from constants import LLM_API_URL, LLM_MODEL

class LLMModule:
    def __init__(self, state: State):
        self.state = state

    def generate_response(self, prompt: str):
        """
        For normal user-facing conversation.
        """
        with self.state.lock:
            self.state.ai_thinking = True

        try:
            payload = {"prompt": prompt, "model": LLM_MODEL, "stream": False}
            print(f"[LLM] Sending user conversation prompt to Ollama.")
            response = requests.post(f"{LLM_API_URL}", json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            ai_response = data.get("response", "")
        except Exception as e:
            print("[LLM] Exception:", e)
            traceback.print_exc()
            ai_response = "(Error retrieving response)"
        finally:
            with self.state.lock:
                self.state.ai_thinking = False

        return ai_response

    def generate_response_for_memory(self, prompt: str):
        """
        Possibly the same or nearly the same as generate_response,
        but you can handle different parameters or system prompts if desired.
        """
        try:
            print("[LLM] Sending memory-summarization prompt to Ollama.")
            payload = {"prompt": prompt, "model": LLM_MODEL, "stream": False}
            response = requests.post(f"{LLM_API_URL}", json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            print("[LLM] Exception in memory summarization:", e)
            traceback.print_exc()
            return "(Error summarizing memory)"
