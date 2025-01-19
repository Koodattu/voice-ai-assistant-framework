# tts.py

import time
import traceback
from state import State
from constants import AUDIO_DEVICE_OUTPUT_ID
# from realtimetts import RealTimeTTS  # If using the real library

class TTSModule:
    def __init__(self, state: State):
        self.state = state
        # self.tts_engine = RealTimeTTS(device_id=AUDIO_DEVICE_OUTPUT_ID)
        # ^ adapt to real usage
        self.pending_responses = []

    def speak(self, text: str):
        """Queue text for TTS playback."""
        self.pending_responses.append(text)

    def run(self):
        """Continuously check for new TTS tasks and speak them."""
        print("[TTS] Starting TTS module.")
        while True:
            with self.state.lock:
                if self.state.shutdown:
                    print("[TTS] Shutting down TTS module.")
                    break

            if self.pending_responses:
                # Let other modules know we're talking
                with self.state.lock:
                    self.state.ai_talking = True

                text_to_speak = self.pending_responses.pop(0)
                try:
                    print(f"[TTS] Speaking: {text_to_speak}")
                    # self.tts_engine.speak(text_to_speak)
                    time.sleep(2)  # simulate speaking duration
                except Exception as e:
                    print("[TTS] Exception:", e)
                    traceback.print_exc()

                # Done talking
                with self.state.lock:
                    self.state.ai_talking = False
            else:
                time.sleep(0.1)
