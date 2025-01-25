# constants.py

# Audio device configuration
AUDIO_DEVICE_INPUT_ID = 1#3#1     # Adjust to your actual device ID for input (where does the AI hear from)
AUDIO_DEVICE_OUTPUT_ID = 32#22#32    # Adjust to your actual device ID for output (where does the AI speak to)
WHISPER_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"  # Model for STT

VOICE_SAMPLE = "./voice-samples/own/niilo.wav"  # Path to the voice sample for TTS

# LLM configuration
LLM_API_URL = "http://localhost:11434/api/generate"  # Example local Ollama instance
LLM_MODEL = "qwen2.5:7b-instruct-q4_K_M"  # Model for LLM
PATIENCE_SECONDS = 50  # Number of seconds to wait before prompting the LLM if no new messages

# MEMORY SECTION: Constants relevant to forming new memories
MEMORY_RECALL_COUNT = 5 # How many memories to recall and insert into context
CHROMA_PERSIST_DIRECTORY = "./chromadb" # Path to ChromaDB persistent storage
MEMORY_INTERVAL = 10 # How many messages before generating a short summary

# The AI assistant's "identity"
AI_NAME = "Merlin"

# A system prompt to guide the AI’s style and behavior
SYSTEM_PROMPT = (
    "You are {AI_NAME}, a friendly AI assistant with a calm, concise style.\n"
    "You should respond to questions or context with short, direct answers.\n"
    "Avoid extra words unless necessary.\n"
)