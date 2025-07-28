
import time
import traceback
import subprocess
from state import State
from config import AUDIO_DEVICE_OUTPUT_ID, VOICE_SAMPLE_WAV, VOICE_SAMPLE_TXT, VOCAB_TXT
from logger import logger
import os
from huggingface_hub import hf_hub_download
import sounddevice as sd
import soundfile as sf

class F5TTSModule:
    def __init__(self, state: State):
        logger.info("F5TTSModule: Initializing F5-TTS module.")
        self.state = state
        self.output_device_index = AUDIO_DEVICE_OUTPUT_ID
        self.voice_sample_wav = VOICE_SAMPLE_WAV
        with open(VOICE_SAMPLE_TXT, "r", encoding="utf-8") as f:
            self.voice_sample_txt = f.read()
        self.vocab_txt = VOCAB_TXT
        self.audio_dir = os.path.join("generated", "audio", "f5tts")
        os.makedirs(self.audio_dir, exist_ok=True)
        logger.info(f"F5TTSModule: Audio output directory set to {self.audio_dir}")

        self.model_path = hf_hub_download(
            repo_id="AsmoKoskinen/F5-TTS_Finnish_Model",
            filename=f"model_commonvoice_fi_librivox_fi_vox_populi_fi_20250323/model_last_20250323.safetensors",
            cache_dir=os.path.join("models", "f5tts"),
        )
        logger.info(f"F5TTSModule: Model file downloaded to {self.model_path}")

    def audio_started(self):
        self.state.ai_talking = True
        logger.info("F5TTSModule: Audio started (AI is speaking).")

    def audio_ended(self):
        self.state.ai_talking = False
        self.state.last_message_timestamp = time.time()
        logger.info("F5TTSModule: Audio ended (AI is done speaking).")

    def compute_speed(self, text):
        word_count = len(text.split())
        if word_count == 2:
            return "0.4"
        elif word_count == 3:
            return "0.6"
        elif word_count == 4:
            return "0.8"
        else:
            return "1"

    def speak(self, text: str):
        if not text.strip():
            logger.debug("F5TTSModule: Empty text provided to speak; ignoring.")
            return

        logger.info(f"F5TTSModule: Speaking text: {text}")
        try:
            # Generate audio file using F5-TTS CLI
            filename = f"f5tts_{int(time.time()*1000)}.wav"
            filepath = os.path.join(self.audio_dir, filename)
            command = [
                "f5-tts_infer-cli",
                "--model", "F5TTS_v1_Base",
                "--ckpt_file", self.model_path,
                "--gen_text", text,
                "-o", self.audio_dir,
                "-w", filename,
                "-v", self.vocab_txt,
                "--ref_text", self.voice_sample_txt,
                "--ref_audio", self.voice_sample_wav,
                "--speed", self.compute_speed(text),
            ]
            logger.debug(f"F5TTSModule: Running command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True)
            logger.info(f"F5TTSModule: Audio generated at {filepath}")
            self.audio_started()
            # Play the audio file using the output device
            self.play_audio(filepath)
            self.audio_ended()
        except subprocess.CalledProcessError as e:
            logger.error(f"F5TTSModule: Error generating audio: {e}")
            logger.debug(e.stderr.decode())
        except Exception as e:
            logger.error(f"F5TTSModule: Error during F5-TTS playback: {e}")
            logger.debug(traceback.format_exc())

    def play_audio(self, filepath):
        logger.info(f"F5TTSModule: Playing audio file {filepath} on device {self.output_device_index}")
        try:
            data, samplerate = sf.read(filepath, dtype='float32')
            sd.play(data, samplerate, device=self.output_device_index)
            sd.wait()  # Wait until playback is finished
        except Exception as e:
            logger.error(f"F5TTSModule: Error playing audio: {e}")

    def run(self):
        logger.info("F5TTSModule: Running F5-TTS module.")
        try:
            while not self.state.shutdown:
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"F5TTSModule: Error during F5-TTS operation: {e}")
            logger.debug(traceback.format_exc())
        finally:
            logger.info("F5TTSModule: Exiting F5-TTS module.")
