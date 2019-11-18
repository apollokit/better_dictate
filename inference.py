""" Thread and utilities for audio input.
"""

import logging
import threading
import time
from queue import Queue, Empty

import numpy as np
from nptyping import Array

from stt import DeepSpeechEngine
from audio import FS, AudioFramesQentry
from utils import json_thing

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def inference_thread(
        audio_frames_q: Queue,
        inference_output_q: Queue,
        shutdown_event: threading.Event,
        output_file: str = 'output.json'):
    """ Execution thread for inference on raw inputs
    
    Waits for audio frames to be put in the queue, then processes them (speech
    to text) and puts them on the output queue. For now, this queue contains
    text output from the speech to text engine.

    Args:
        audio_frames_q: output queue for captured audio frames. Each entry is
            a numpy Array[np.int16]
        inference_output_q: contains output string text from the text to speech
            engine.
        shutdown_event: event used to signal shutdown across threads
        output_file: path of file in which to store benchmark output from
            inference
    """
    logger.info(f"Starting DeepSpeechEngine")
    engine = DeepSpeechEngine('config_deepspeech.yaml')
    # the main thread loop. Go forever.
    logger.info(f"DeepSpeechEngine ready")
    file_output_stuff = {}
    iinf = 0
    while True:
        try:
            q_entry: AudioFramesQentry = audio_frames_q.get(
                block=True, timeout=0.1)
            
            logger.debug(f"Got frames from audio_frames_q")
            start = time.time()
            frames = np.frombuffer(b''.join(q_entry.frames), np.int16)
            text = engine.transform(frames, FS)
            logger.debug(text)
            end = time.time()
            inference_time = end - start
            logger.debug(f"Took {inference_time:0.2f} seconds for "
                f"{q_entry.duration:0.2f} audio")
            file_output_stuff[iinf] = {
                "audio_duration": q_entry.duration,
                "inference_time": inference_time,
                "inference_result": text,
                }
            inference_output_q.put(text)
            iinf += 1
        # queue was empty up to timeout
        except Empty:
            # check if it's time to close shop
            if shutdown_event.is_set():
                break

    logger.info(f"Writing inference output file {output_file}")
    json_thing(file_output_stuff, output_file)


        

