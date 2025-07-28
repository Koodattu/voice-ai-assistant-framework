# Audio device configuration
AUDIO_DEVICE_INPUT_ID = 1     # Adjust to your actual device ID for input (where does the AI hear from)
AUDIO_DEVICE_OUTPUT_ID = 32    # Adjust to your actual device ID for output (where does the AI speak to)
WHISPER_MODEL = "turbo"  # Model for STT

VOICE_SAMPLE_WAV = "./voice-data/ref_fin.wav"  # Path to the voice sample for TTS
VOICE_SAMPLE_TXT = "./voice-data/ref_fin.txt"  # Path to the text sample for F5-TTS
VOCAB_TXT = "./voice-data/vocab_fin.txt"  # Vocabulary file for F5-TTS

# LLM configuration
LLM_API_URL = "http://localhost:11434/api/generate"  # Example local Ollama instance
LLM_MODEL = "hf.co/mradermacher/Llama-Poro-2-8B-Instruct-GGUF:Q4_K_M"  # Model for LLM

# AI operational modes
AI_MODE_CONVERSATION = "conversation"
AI_MODE_DISCUSSION = "discussion"

# Choose the default mode here:
AI_MODE = AI_MODE_CONVERSATION  # or AI_MODE_DISCUSSION

AI_NAME = "Juha"

# A system prompt to guide the AI’s style and behavior; we incorporate the modes.
SYSTEM_PROMPT = (
    "You are {AI_NAME}, an AI assistant."
    "You are helpful, friendly and slightly sarcastic."
    "You have two modes:\n"
    "- conversation: You always respond to user messages (shortly)\n"
    "- discussion: You speak only if your name is mentioned or if a long silence passed.\n"
    "You also maintain an internal monologue or 'notebook' that is not spoken.\n"
    "Please put any longer reasoning or chain-of-thought inside 'internalMonologue'."
    "Keep 'reply' short unless you are asked for a longer explanation by name or the conversation mode is 'conversation'."
    "Set 'wantsToSpeak' to true if you want to speak the 'reply'."
    "Your output must be valid JSON with these fields:\n"
    "  wantsToSpeak: boolean\n"
    "  reply: short or long string (the spoken reply if wantsToSpeak == true)\n"
    "  internalMonologue: longer text describing your thoughts\n"
    "Current mode is: {AI_MODE}\n"
    "Please write the reply in same language as the user is speaking.\n"
    "IMPORTANT: Output ONLY valid JSON, no extra text.\n"
)

# For Ollama's structured output feature, we can define a schema:
OLLAMA_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "wantsToSpeak": {"type": "boolean"},
        "reply": {"type": "string"},
        "internalMonologue": {"type": "string"}
    },
    "required": ["wantsToSpeak", "reply", "internalMonologue"]
}

INITIAL_GREETING_DELAY = 3  # seconds

# Silence threshold in seconds
SILENCE_THRESHOLD = 15  # seconds, how long to wait before generating a response if no user input