# constants.py

# Audio device configuration
AUDIO_DEVICE_INPUT_ID = 3#1     # Adjust to your actual device ID for input (where does the AI hear from)
AUDIO_DEVICE_OUTPUT_ID = 22#32    # Adjust to your actual device ID for output (where does the AI speak to)
WHISPER_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"  # Model for STT

VOICE_SAMPLE = "./voice-sample/own/juha.wav"  # Path to the voice sample for TTS

# LLM configuration
LLM_API_URL = "http://localhost:11434/api/generate"  # Example local Ollama instance
LLM_MODEL = "qwen2.5:7b-instruct-q4_K_M"  # Model for LLM
PATIENCE_SECONDS = 50  # Number of seconds to wait before prompting the LLM if no new messages

# MEMORY SECTION: Constants relevant to forming new memories
MEMORY_RECALL_COUNT = 5 # How many memories to recall and insert into context
CHROMA_PERSIST_DIRECTORY = "./chromadb" # Path to ChromaDB persistent storage
REFLECTION_IMPORTANCE_THRESHOLD = 20  # If recent memories' cumulative importance exceeds this, trigger reflection
RECENCY_DECAY_FACTOR = 1.0 / 3600     # Example decay factor for recency (1/hour)
IMPORTANCE_WEIGHT = 1.0
RECENCY_WEIGHT = 1.0
RELEVANCE_WEIGHT = 1.0
MAX_RETRIEVAL_RESULTS = 50            # Number of results to retrieve before custom scoring