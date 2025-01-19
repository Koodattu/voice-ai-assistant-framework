# stt.py

import time
import traceback
from state import State
from constants import AUDIO_DEVICE_INPUT_ID
# from realtimestt import RealTimeSTT  # If using the real library

class STTModule:
    def __init__(self, state: State):
        self.state = state
        # self.stt_engine = RealTimeSTT(device_id=AUDIO_DEVICE_INPUT_ID)
        # ^ adapt to real usage

    def run(self):
        """Continuously capture audio and convert to text."""
        print("[STT] Starting STT module.")
        while True:
            # Check if we need to shut down
            with self.state.lock:
                if self.state.shutdown:
                    print("[STT] Shutting down STT module.")
                    break

            try:
                # Example:
                # text = self.stt_engine.listen()
                # if text:
                #     print(f"[STT] Transcribed text: {text}")
                #     self.state.add_new_message(text)
                
                # Simulated placeholder (replace with real STT logic):
                time.sleep(2)  # pretend we blocked waiting for speech
                simulated_text = "User said something..."
                print(f"[STT] Transcribed text: {simulated_text}")
                self.state.add_new_message(simulated_text)

            except Exception as e:
                print("[STT] Exception:", e)
                traceback.print_exc()
                time.sleep(1)
