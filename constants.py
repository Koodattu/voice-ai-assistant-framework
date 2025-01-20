# constants.py

# Audio device configuration
AUDIO_DEVICE_INPUT_ID = 1     # Adjust to your actual device ID for input (microphone)
AUDIO_DEVICE_OUTPUT_ID = 32    # Adjust to your actual device ID for output (speaker)
WHISPER_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"  # Model for STT

# LLM configuration
LLM_API_URL = "http://localhost:11411"  # Example local Ollama instance
PATIENCE_SECONDS = 50  # Number of seconds to wait before prompting the LLM if no new messages
