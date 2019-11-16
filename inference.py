""" Thread and utilities for audio input.
"""

import logging
import time
import queue

import numpy as np
from nptyping import Array

from stt import DeepSpeechEngine
from audio import FS, AudioFramesQentry

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def inference_thread(
        audio_frames_q: queue.Queue,
        inference_output_q: queue.Queue):
    """ Execution thread for inference on raw inputs
    
    Waits for audio frames to be put in the queue, then processes them (speech
    to text) and puts them on the output queue. For now, this queue contains
    text output from the speech to text engine.

    Args:
        audio_frames_q: output queue for captured audio frames. Each entry is
            a numpy Array[np.int16]
        inference_output_q: contains output string text from the text to speech
            engine.
    """

    logger.info(f"Starting DeepSpeechEngine")
    engine = DeepSpeechEngine('config_deepspeech.yaml')
    # the main thread loop. Go forever.
    while True:
        logger.info(f"DeepSpeechEngine ready")
        q_entry: AudioFramesQentry = audio_frames_q.get(block=True)
        logger.debug(f"Got frames from audio_frames_q")
        start = time.time()
        frames = np.frombuffer(b''.join(q_entry.frames), np.int16)
        text = engine.transform(frames, FS)
        logger.debug(text)
        end = time.time()
        logger.debug(f"Took {end - start:0.2f} seconds for "
            f"{q_entry.duration:0.2f} audio")
        
        inference_output_q.put(text)

