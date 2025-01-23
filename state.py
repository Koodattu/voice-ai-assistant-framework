# state.py

import threading
import time

class State:
    def __init__(self):
        self.lock = threading.RLock()
        self.shutdown = False

        # Flags
        self.user_talking = False
        self.ai_talking = False
        self.ai_thinking = False

        # Store newly transcribed messages here
        self.new_messages = []
        
        # Track last message time for "patience" logic
        self.last_message_timestamp = time.time()

    def add_new_message(self, message: str):
        """Thread-safe way to add a new user message."""
        with self.lock:
            self.new_messages.append(message)
            self.last_message_timestamp = time.time()
