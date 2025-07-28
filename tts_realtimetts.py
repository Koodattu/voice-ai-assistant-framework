import time
import traceback
from state import State
from config import AUDIO_DEVICE_OUTPUT_ID, VOICE_SAMPLE_WAV
from RealtimeTTS import TextToAudioStream, CoquiEngine
from logger import logger

class TTSModule:
    def __init__(self, state: State):
        logger.info("TTSModule: Initializing TTS module.")
        self.state = state
        try:
            engine = CoquiEngine(
                use_deepspeed=True,
                voice=VOICE_SAMPLE_WAV,
                speed=1,
            )
            logger.info("TTSModule: CoquiEngine initialized successfully.")
        except Exception as e:
            logger.error(f"TTSModule: Failed to initialize CoquiEngine: {e}")
            self.stream = None
            return

        tts_config = {
            'on_audio_stream_start': self.audio_started,
            'on_audio_stream_stop': self.audio_ended,
            'output_device_index': AUDIO_DEVICE_OUTPUT_ID,
        }

        try:
            self.stream = TextToAudioStream(engine, **tts_config)
            logger.info("TTSModule: TextToAudioStream initialized successfully.")
        except Exception as e:
            logger.error(f"TTSModule: Failed to initialize TextToAudioStream: {e}")
            self.stream = None
            return

    def audio_started(self):
        self.state.ai_talking = True
        logger.info("TTSModule: Audio started (AI is speaking).")

    def audio_ended(self):
        self.state.ai_talking = False
        self.state.last_message_timestamp = time.time()
        logger.info("TTSModule: Audio ended (AI is done speaking).")

    def speak(self, text: str):
        if not self.stream:
            logger.warning("TTSModule: TextToAudioStream not initialized. Cannot speak.")
            return

        if not text.strip():
            logger.debug("TTSModule: Empty text provided to speak; ignoring.")
            return

        logger.info(f"TTSModule: Speaking text: {text}")
        try:
            self.stream.feed(text)
            self.stream.play_async()
            logger.debug("TTSModule: Text fed to TTS stream and playback started.")
        except Exception as e:
            logger.error(f"TTSModule: Error during TTS playback: {e}")
            logger.debug(traceback.format_exc())

    def run(self):
        logger.info("TTSModule: Running TTS module.")
        try:
            while not self.state.shutdown:
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"TTSModule: Error during TTS operation: {e}")
            logger.debug(traceback.format_exc())
        finally:
            logger.info("TTSModule: Exiting TTS module.")
