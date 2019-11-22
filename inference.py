""" Thread and utilities for audio input.
"""

from halo import Halo
import logging
import threading
import time
from queue import Queue, Empty
from typing import Optional

import numpy as np
from nptyping import Array

from stt import DeepSpeechEngine
from audio import SAMPLE_RATE
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

    A lot of code drawn from https://github.com/mozilla/DeepSpeech/blob/master/examples/mic_vad_streaming/mic_vad_streaming.py

    Args:
        audio_frames_q: output queue for captured frames. Each entry will be a
            bytes, or None to indicate the end of an utterance
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

    spinner = None
    spinner = Halo(spinner='line')
    stream_start = time.time()
    engine.new_stream()
    while True:
        try:
            frame: Optional[bytes] = audio_frames_q.get(
                block=True, timeout=0.1)
            # while still getting frames in utterance
            if frame is not None:
                if spinner: spinner.start()
                engine.feed_stream(frame)
            # end of utterance
            else:
                if spinner: spinner.stop()
                logger.debug("End utterence")
                text = engine.end_stream()
                stream_end = time.time()
                logger.debug(f"Recognized: {text}")
                logger.debug(f'Time taken: {stream_end - stream_start:.2f}')
                file_output_stuff[iinf] = {
                    "audio_inference_time": stream_end-stream_start,
                    "inference_result": text,
                }
                inference_output_q.put(text)
                iinf += 1
                stream_start = time.time()
                engine.new_stream()
            
        # queue was empty up to timeout
        except Empty:
            # check if it's time to close shop
            if shutdown_event.is_set():
                if spinner: spinner.stop()
                # end the stream and throw out the text
                engine.end_stream()
                break

    logger.info(f"Writing inference output file {output_file}")
    json_thing(file_output_stuff, output_file)


        

