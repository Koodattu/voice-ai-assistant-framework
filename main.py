# main.py

import threading
import time
import signal

from state import State
from stt import STTModule
from tts import TTSModule
from llm import LLMModule
from orchestrator import Orchestrator

def main():
    print("[Main] Starting...")
    state = State()

    print("[Main] Creating modules...")
    # Create module instances
    stt_module = STTModule(state)
    tts_module = TTSModule(state)
    llm_module = LLMModule(state)
    orchestrator = Orchestrator(state, llm_module, tts_module)

    print("[Main] Starting threads...")
    # Threads
    stt_thread = threading.Thread(target=stt_module.run, name="STTThread", daemon=True)
    tts_thread = threading.Thread(target=tts_module.run, name="TTSThread", daemon=True)
    orchestrator_thread = threading.Thread(target=orchestrator.run, name="OrchestratorThread", daemon=True)

    print("[Main] Starting modules...")
    # Start
    stt_thread.start()
    tts_thread.start()
    orchestrator_thread.start()

    # Handle Ctrl+C
    def signal_handler(sig, frame):
        print("[Main] Caught Ctrl+C, requesting shutdown...")
        with state.lock:
            state.shutdown = True

    signal.signal(signal.SIGINT, signal_handler)

    print("[Main] Ready. Press Ctrl+C to exit.")
    # Main thread wait loop
    try:
        while True:
            time.sleep(0.5)
            with state.lock:
                if state.shutdown:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        print("[Main] Joining threads...")
        stt_thread.join()
        tts_thread.join()
        orchestrator_thread.join()
        print("[Main] Shutdown complete.")

if __name__ == "__main__":
    main()
