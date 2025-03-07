# main.py
import threading
import time
import signal
from logger import logger
from constants import AI_NAME
from state import State
from stt import STTModule
from tts import TTSModule
from orchestrator import Orchestrator
from memory import MemoryManager
from whatsapp.whatsapp import run_whatsapp  # Import the WhatsApp function

def main():
    logger.info("Main: Starting the system.")
    state = State()

    logger.info("Main: Creating modules.")
    # Create module instances
    stt_module = STTModule(state)
    tts_module = TTSModule(state)
    memory_manager = MemoryManager(state)
    orchestrator = Orchestrator(state, tts_module, memory_manager)

    logger.info("Main: Starting threads.")
    # Threads for the various modules
    stt_thread = threading.Thread(target=stt_module.run, name="STTThread", daemon=True)
    tts_thread = threading.Thread(target=tts_module.run, name="TTSThread", daemon=True)
    memory_thread = threading.Thread(target=memory_manager.run, name="MemoryThread", daemon=True)
    orchestrator_thread = threading.Thread(target=orchestrator.run, name="OrchestratorThread", daemon=True)
    whatsapp_thread = threading.Thread(target=run_whatsapp, args=(state,), name="WhatsAppThread", daemon=True)

    logger.info("Main: Starting module threads.")
    stt_thread.start()
    tts_thread.start()
    memory_thread.start()
    orchestrator_thread.start()
    whatsapp_thread.start()

    # Handle Ctrl+C
    def signal_handler(sig, frame):
        logger.info("Main: Caught Ctrl+C, requesting shutdown...")
        state.shutdown = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Main: System is ready. Press Ctrl+C to exit.")
    tts_module.speak(f"Hello, I am {AI_NAME}, your AI assistant. Please join a call to start.")
    state.last_message_timestamp = time.time()
    state.system_ready = True

    # Main thread wait loop
    try:
        while not state.shutdown:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Main: KeyboardInterrupt received.")
    finally:
        logger.info("Main: Shutdown signal received. Waiting for threads to finish...")
        logger.info("Main: Shutdown complete.")

if __name__ == "__main__":
    main()
