import time
import logging
from state import State
from config import AUDIO_DEVICE_INPUT_ID, WHISPER_MODEL
from RealtimeSTT import AudioToTextRecorder
import traceback
from logger import logger

class STTModule:
    def __init__(self, state: State):
        logger.info("STTModule: Initializing STT module.")
        self.state = state

        recorder_config = {
            'spinner': False,
            'model': WHISPER_MODEL,
            'use_microphone': True,
            'input_device_index': AUDIO_DEVICE_INPUT_ID,
            'silero_sensitivity': 0.6,
            'silero_use_onnx': True,
            'post_speech_silence_duration': 0.6,
            'min_length_of_recording': 0.0,
            'min_gap_between_recordings': 0.2,
            'enable_realtime_transcription': True,
            'on_realtime_transcription_stabilized': self.realtime_stabilized,
            'on_realtime_transcription_update': self.realtime_update,
            'realtime_model_type': 'small',
            'compute_type': 'auto',
            'on_recording_start': self.recording_start,
            'on_recording_stop': self.recording_stop,
            'level': logging.ERROR
        }

        try:
            self.recorder = AudioToTextRecorder(**recorder_config)
            logger.info("STTModule: Recorder initialized successfully.")
        except Exception as e:
            logger.error(f"STTModule: Failed to initialize AudioToTextRecorder: {e}")
            self.recorder = None

    def realtime_stabilized(self, text: str):
        logger.info(f"STTModule: Realtime transcription stabilized: {text}")

    def realtime_update(self, text: str):
        logger.debug(f"STTModule: Realtime transcription update: {text}")

    def recording_start(self):
        logger.info("STTModule: Recording started.")
        self.state.user_talking = True
        logger.debug("STTModule: Set state user_talking to True.")

    def recording_stop(self):
        logger.info("STTModule: Recording stopped.")
        self.state.user_talking = False
        logger.debug("STTModule: Set state user_talking to False.")

    def process_text(self, text: str):
        text = text.strip()
        if not text:
            logger.debug("STTModule: Empty transcription received; ignoring.")
            return

        logger.info(f"STTModule: Transcribed text received: {text}")
        self.state.add_new_message(text)
        logger.debug("STTModule: Added new message to state.")

    def run(self):
        logger.info("STTModule: Running STT module.")
        try:
            while not self.state.shutdown:
                if self.recorder:
                    self.recorder.text(self.process_text)
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"STTModule: Error during transcription: {e}")
            logger.debug(traceback.format_exc())
        finally:
            logger.info("STTModule: Exiting STT module.")
