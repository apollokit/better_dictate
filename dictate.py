""" Main script for the dictation tool
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import logging
import time
import threading
import queue

import click 
import numpy as np
from nptyping import Array
from pynput import keyboard
import wave

from keyboard import keyboard_audio_event, keyb_listener
from audio import audio_thread, read_audio_from_file
from inference import DeepSpeechEngine

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@click.group()
def cli():
    pass

@cli.command()
@click.option("--audio_file", type=str, default=None,
    help="Path to an audio file. If provided, inference will be run on it and"
    "then the script will exit.")
def go(
    audio_file: str
    ):
    logging.info('Starting up')

    # engine = DeepSpeechEngine('config_deepspeech.yaml')

    # if we're just doing speech to text on an input audio file
    if audio_file is not None:
        audio, audio_length = read_audio_from_file(audio_file)

        start = time.time()
        text = engine.transform(audio, fs)
        print(text)
        end = time.time()
        print(f"Took {end - start:.2f}s for stt on {audio_length:.2f}s input")
        return

    # interactive stuff

    # data structures for inter-thread communication
    # queue for captured audio frames
    audio_frames_q = queue.Queue()

    keyb_listener.start()

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []
        futures.append(executor.submit(
            audio_thread, 
            keyboard_audio_event, 
            audio_frames_q))
        for future in as_completed(futures):
            logger.debug(repr(future.exception()))


    # start = time.time()
    # # text = engine.transform(frames, fs)
    # frames = np.frombuffer(b''.join(frames), np.int16)
    # out = engine._model.stt(frames, fs)
    # print(out)
    # end = time.time()
    # print(f"Took {end - start} seconds")

    # # Save the recorded data as a WAV file
    # wf = wave.open(/home/kit/Desktop/projects/better_dictate/audio/2830-3980-0043.wav, 'wb')
    # wf.setnchannels(channels)
    # wf.setsampwidth(p.get_sample_size(sample_format))
    # wf.setframerate(fs)
    # wf.writeframes(b''.join(frames))
    # wf.close()

    # print(f'File written: {filename}')

if __name__ == '__main__':
    cli()