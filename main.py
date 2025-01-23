import threading
import time
import signal
from logger import logger

from state import State
from stt import STTModule
from tts import TTSModule
from llm import LLMModule
from orchestrator import Orchestrator
from memory import MemoryManager

def main():
    logger.info("Main: Starting the system.")
    state = State()

    logger.info("Main: Creating modules.")
    # Create module instances
    stt_module = STTModule(state)
    tts_module = TTSModule(state)
    llm_module = LLMModule(state)
    memory_manager = MemoryManager(state)
    orchestrator = Orchestrator(state, llm_module, tts_module, memory_manager)

    logger.info("Main: Starting threads.")
    # Threads
    stt_thread = threading.Thread(target=stt_module.run, name="STTThread", daemon=True)
    tts_thread = threading.Thread(target=tts_module.run, name="TTSThread", daemon=True)
    orchestrator_thread = threading.Thread(target=orchestrator.run, name="OrchestratorThread", daemon=True)
    memory_thread = threading.Thread(target=memory_manager.run, name="MemoryThread", daemon=True)

    logger.info("Main: Starting module threads.")
    # Start threads
    stt_thread.start()
    tts_thread.start()
    orchestrator_thread.start()
    memory_thread.start()

    # Handle Ctrl+C
    def signal_handler(sig, frame):
        logger.info("Main: Caught Ctrl+C, requesting shutdown...")
        state.shutdown = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Main: System is ready. Press Ctrl+C to exit.")
    # Main thread wait loop
    try:
        while not state.shutdown:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Main: KeyboardInterrupt received.")
    finally:
        logger.info("Main: Shutdown signal received. Waiting for threads to finish...")
        # Threads are daemons and will exit automatically
        logger.info("Main: Shutdown complete.")

if __name__ == "__main__":
    main()
