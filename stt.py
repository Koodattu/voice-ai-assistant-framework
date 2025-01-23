# stt.py

import time
import traceback
import logging
from state import State
from constants import AUDIO_DEVICE_INPUT_ID, WHISPER_MODEL
from RealtimeSTT import AudioToTextRecorder

# Adjust logging level if desired
logging.basicConfig(level=logging.ERROR)

class STTModule:
    def __init__(self, state: State):
        print("[STT] Initializing STT module.")
        self.state = state
        self.recorder = None  # Will be initialized in run()

    def recording_start(self):
        """Callback when recording starts."""
        print("[STT] Recording started.")
        with self.state.lock:
            self.state.user_talking = True
            print("[STT] Set state user_talking: True.")

    def recording_stop(self):
        """Callback when recording stops."""
        print("[STT] Recording stopped.")
        with self.state.lock:
            self.state.user_talking = False
            print("[STT] Set state user_talking: False.")

    def process_text(self, text: str):
        """Process the recognized text by sending it to the shared state."""
        # Simple pre-processing: trim and ignore empty text.
        text = text.strip()
        if not text:
            return

        print("[STT] Transcribed text:", text)
        # Update the timestamp for new messages.
        with self.state.lock:
            self.state.add_new_message(text)
            self.state.last_message_timestamp = time.time()
            print("[STT] Added new message to state.")

    def run(self):
        """Continuously capture audio and convert to text."""
        print("[STT] Starting STT module.")

        # Configure the recorder using parameters selected from our examples.
        # These parameters are a balance between responsiveness and accuracy.
        recorder_config = {
            'spinner': False,
            'model': WHISPER_MODEL,
            'use_microphone': True,
            'input_device_index': AUDIO_DEVICE_INPUT_ID,  # using our constant
            'silero_sensitivity': 0.6,
            'silero_use_onnx': True,
            'post_speech_silence_duration': 2.4,  # adjust as needed
            'min_length_of_recording': 0.0,
            'min_gap_between_recordings': 0.2,
            'enable_realtime_transcription': False,
            'compute_type': 'auto',
            'on_recording_start': self.recording_start,
            'on_recording_stop': self.recording_stop,
            'level': logging.ERROR
        }

        try:
            # Use the recorder as a context manager.
            with AudioToTextRecorder(**recorder_config) as recorder:
                self.recorder = recorder
                print("[STT] Recorder ready. Listening for speech...")
                while True:
                    # Check for shutdown signal
                    with self.state.lock:
                        if self.state.shutdown:
                            print("[STT] Shutdown signal received.")
                            break

                    # The recorder's .text() method calls our process_text() callback whenever new
                    # transcription output is available.
                    recorder.text(self.process_text)
                    time.sleep(0.1)
        except Exception as e:
            print("[STT] Exception:", e)
            traceback.print_exc()
            time.sleep(1)

        print("[STT] Exiting STT module.")
