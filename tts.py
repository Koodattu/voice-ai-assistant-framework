# tts.py

import time
import traceback
import logging
from state import State
from constants import AUDIO_DEVICE_OUTPUT_ID
from RealtimeTTS import TextToAudioStream, CoquiEngine

logging.basicConfig(level=logging.ERROR)

class TTSModule:
    def __init__(self, state: State):
        print("[TTS] Initializing TTS module.")
        self.state = state
        self.pending_responses = []  # Queue for text to speak
        # Initialize the TTS engine.
        # Here we “train” the engine with a voice sample.
        # Adjust the voice path and parameters as desired.
        try:
            self.engine = CoquiEngine(
                #use_deepspeed=True,
                # The engine will load and prepare the voice-sample.
                voice="voice-sample.wav",  # path to your voice sample file
                speed=1.0  # Adjust synthesis speed as needed
            )
        except Exception as e:
            print("[TTS] Failed to initialize CoquiEngine:", e)
            raise

        # Configure the stream.
        # The callbacks will update the shared state (ai_talking).
        tts_config = {
            'on_audio_stream_start': self.audio_started,
            'on_audio_stream_stop': self.audio_ended,
            'output_device_index': AUDIO_DEVICE_OUTPUT_ID,
        }
        self.stream = TextToAudioStream(self.engine, **tts_config)
        print("[TTS] TTS engine and stream initialized.")

    def audio_started(self):
        """Callback called when audio stream starts playing."""
        with self.state.lock:
            self.state.ai_talking = True
        print("[TTS] Audio started (AI is speaking).")

    def audio_ended(self):
        """Callback called when audio stream stops playing."""
        with self.state.lock:
            self.state.ai_talking = False
            self.state.last_message_timestamp = time.time()
        print("[TTS] Audio ended (AI is done speaking).")

    def speak(self, text: str):
        """Queue text for TTS playback."""
        self.pending_responses.append(text)

    def run(self):
        """Continuously check for new TTS tasks and speak them."""
        print("[TTS] Starting TTS module.")
        while True:
            # Check for shutdown
            with self.state.lock:
                if self.state.shutdown:
                    print("[TTS] Shutting down TTS module.")
                    break

            if self.pending_responses:
                # Mark state: AI is about to speak.
                with self.state.lock:
                    self.state.ai_talking = True

                text_to_speak = self.pending_responses.pop(0)
                try:
                    print(f"[TTS] Speaking: {text_to_speak}")
                    # Feed text to the stream and play asynchronously.
                    self.stream.feed(text_to_speak)
                    self.stream.play_async()
                    # Optionally: wait a little if you want to avoid overlapping texts.
                    # Here we wait until playback appears to have finished.
                    while self.stream.is_playing():
                        time.sleep(0.1)
                except Exception as e:
                    print("[TTS] Exception during TTS playback:", e)
                    traceback.print_exc()

                # Reset the flag after speaking.
                with self.state.lock:
                    self.state.ai_talking = False
            else:
                time.sleep(0.1)
