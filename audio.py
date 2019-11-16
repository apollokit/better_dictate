""" Thread and utilities for audio input.
"""

import logging
import threading
import time
from queue import Queue

import numpy as np
from nptyping import Array
import pyaudio

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CHUNK = 1024  # Record in chunks of 1024 samples
SAMPLE_FORMAT = pyaudio.paInt16  # 16 bits per sample
CHANNELS = 1 # record in mono
FS = 16000   # Record at 16k samples per second

class AudioFramesQentry():
     """docstring for AudioFramesQentry"""
     def __init__(self, frames: Array[np.int16], duration: float):
         self.frames = frames
         self.duration = duration
          
def audio_thread(
        audio_ctrl: threading.Event,
        audio_frames_q: Queue,
        shutdown_event: threading.Event):
    """ Execution thread for audio input
    
    Waits for the audio_ctrl event to be set and then reads frames for as long as it
    is set. Puts those frames into an output queue for further processing.
    
    Args:
        audio_ctrl: when set, audio frame will be read in
        audio_frames_q: output queue for captured frames. Each entry will be a
            numpy Array[np.int16]
        shutdown_event: event used to signal shutdown across threads
    """

    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    # the main thread loop. Go forever.
    while True:
        # check if it's time to close shop
        if shutdown_event.is_set(): 
            break
        if audio_ctrl.is_set():
            # only start recording once the control signal is sent
            logger.info('Recording')
            stream = p.open(format=SAMPLE_FORMAT,
                channels=CHANNELS,
                rate=FS,
                frames_per_buffer=CHUNK,
                input=True)
            
            # Initialize array to store frames. 
            frames: Array[np.int16] = []
            
            # Store data in chunks for as long as the control signal is on
            start = time.time()
            while audio_ctrl.is_set():
                data = stream.read(CHUNK)
                frames.append(data)
            end = time.time()

            # Stop and close the stream 
            stream.stop_stream()
            stream.close()

            logger.info('Finished recording')
            audio_frames_q.put(
                AudioFramesQentry(frames, end-start)
            )

        # 40 msec seems like a good wait time
        time.sleep(0.040)

    # Terminate the PortAudio interface
    p.terminate()

def read_audio_from_file(audio_file: str) -> Array[np.int16]:
    """Reads audio from a .wav file
    
    From deepspeech/client.py

    Args:
        audio_file: path to the audio file
    
    Returns:
        [description]
        Array[np.int16]
    
    Raises:
        Error: [description]
    """
    fin = wave.open(audio_file, 'rb')
    FS = fin.getframerate()
    if FS != 16000:
        raise Error('Warning: original sample rate ({}) is different than 16kHz.'
            'Resampling might produce erratic speech recognition.'.format(FS))
    else:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
        audio_length = fin.getnframes() * (1/16000)
        fin.close()
        return audio, audio_length
