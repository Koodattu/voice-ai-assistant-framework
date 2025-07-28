import time
from logger import logger

class State:
    def __init__(self):
        self.shutdown = False
        self.system_ready = False

        # Flags for conversation/processing
        self.user_talking = False
        self.ai_talking = False
        self.ai_thinking = False

        # Store newly transcribed messages here
        self.new_messages = []

        # Short-term memory: list of recent messages (max 10 messages)
        self.short_term = []
        self.user_message_count = 0

        self.last_message_timestamp = time.time()

        logger.debug("State: Initialized new state.")

    def add_new_message(self, message: str):
        """Add a new user message."""
        self.new_messages.append(message)
        self.short_term.append(f"User: {message}")
        self.user_message_count += 1
        self.last_message_timestamp = time.time()
        logger.debug(f"State: Added new message: {message}")

        # Keep short-term memory within a limit (e.g., last 10 messages)
        if len(self.short_term) > 10:
            removed = self.short_term.pop(0)
            logger.debug(f"State: Removed oldest short-term message: {removed}")
