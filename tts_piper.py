import time
import traceback
import os
from state import State
from config import AUDIO_DEVICE_OUTPUT_ID
from logger import logger
from huggingface_hub import hf_hub_download
from piper import PiperVoice, SynthesisConfig
import sounddevice as sd
import soundfile as sf
import wave
import numpy as np

class PiperTTSModule:
    def __init__(self, state: State):
        logger.info("PiperTTSModule: Initializing Piper TTS module.")
        self.state = state
        self.output_device_index = AUDIO_DEVICE_OUTPUT_ID
        self.audio_dir = os.path.join("generated", "audio", "piper")
        os.makedirs(self.audio_dir, exist_ok=True)
        logger.info(f"PiperTTSModule: Audio output directory set to {self.audio_dir}")

        # Download ONNX model and JSON config from HuggingFace
        model_dir = os.path.join("models", "piper")
        self.model_path = hf_hub_download(
            repo_id="AsmoKoskinen/Piper_Finnish_Model",
            filename="fi_FI-asmo-medium.onnx",
            cache_dir=model_dir,
        )
        self.json_path = hf_hub_download(
            repo_id="AsmoKoskinen/Piper_Finnish_Model",
            filename="fi_FI-asmo-medium.onnx.json",
            cache_dir=model_dir,
        )
        logger.info(f"PiperTTSModule: Model file downloaded to {self.model_path}")
        logger.info(f"PiperTTSModule: JSON config file downloaded to {self.json_path}")
        try:
            self.voice = PiperVoice.load(self.model_path, use_cuda=True)
            logger.info("PiperTTSModule: PiperVoice loaded successfully.")
        except Exception as e:
            logger.error(f"PiperTTSModule: Failed to load PiperVoice: {e}")
            self.voice = None

    def audio_started(self):
        self.state.ai_talking = True
        logger.info("PiperTTSModule: Audio started (AI is speaking).")

    def audio_ended(self):
        self.state.ai_talking = False
        self.state.last_message_timestamp = time.time()
        logger.info("PiperTTSModule: Audio ended (AI is done speaking).")

    def speak(self, text: str):
        if not self.voice:
            logger.warning("PiperTTSModule: PiperVoice not initialized. Cannot speak.")
            return
        if not text.strip():
            logger.debug("PiperTTSModule: Empty text provided to speak; ignoring.")
            return
        logger.info(f"PiperTTSModule: Speaking text: {text}")
        try:
            filename = f"piper_{int(time.time()*1000)}.wav"
            filepath = os.path.join(self.audio_dir, filename)
            syn_config = SynthesisConfig(
                volume=1.0,
                noise_scale=0.5,
                noise_w_scale=0.5,
                normalize_audio=True,
            )
            audio_chunks = self.voice.synthesize(text, syn_config=syn_config)
            audio_arrays = []
            sample_rate = None
            for chunk in audio_chunks:
                if sample_rate is None:
                    sample_rate = chunk.sample_rate
                audio_arrays.append(chunk.audio_float_array)
            audio = np.concatenate(audio_arrays)
            if len(audio.shape) == 1:
                audio = np.expand_dims(audio, axis=1)
            sf.write(filepath, audio, sample_rate)
            logger.info(f"PiperTTSModule: Audio generated at {filepath}")
            self.audio_started()
            self.play_audio(filepath)
            self.audio_ended()
        except Exception as e:
            logger.error(f"PiperTTSModule: Error during Piper TTS playback: {e}")
            logger.debug(traceback.format_exc())

    def play_audio(self, filepath):
        logger.info(f"PiperTTSModule: Playing audio file {filepath} on device {self.output_device_index}")
        try:
            data, samplerate = sf.read(filepath, dtype='float32')
            sd.play(data, samplerate, device=self.output_device_index)
            sd.wait()
        except Exception as e:
            logger.error(f"PiperTTSModule: Error playing audio: {e}")

    def run(self):
        logger.info("PiperTTSModule: Running Piper TTS module.")
        try:
            while not self.state.shutdown:
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"PiperTTSModule: Error during Piper TTS operation: {e}")
            logger.debug(traceback.format_exc())
        finally:
            logger.info("PiperTTSModule: Exiting Piper TTS module.")
