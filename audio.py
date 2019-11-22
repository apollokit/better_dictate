""" Thread and utilities for audio input.
"""

import collections
import logging
from queue import Queue
import threading
import time
import wave
import webrtcvad

import numpy as np
from nptyping import Array
import pyaudio

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# CHUNK = 1024  # Record in chunks of 1024 samples
# CHUNK = 320  # Record in chunks of 320 samples
SAMPLE_FORMAT = pyaudio.paInt16  # 16 bits per sample
CHANNELS = 1 # record in mono
SAMPLE_RATE = 16000   # Record at 16k samples per second

BLOCKS_PER_SECOND = 50
CHUNK = int(SAMPLE_RATE / BLOCKS_PER_SECOND)
          
def audio_thread(
        audio_ctrl: threading.Event,
        audio_frames_q: Queue,
        shutdown_event: threading.Event):
    """ Execution thread for audio input
    
    Waits for the audio_ctrl event to be set and then reads frames for as long as it
    is set. Puts those frames into an output queue for further processing.
    
    A lot of code drawn from https://github.com/mozilla/DeepSpeech/blob/master/examples/mic_vad_streaming/mic_vad_streaming.py

    Args:
        audio_ctrl: when set, audio frame will be read in
        audio_frames_q: output queue for captured frames. Each entry will be a
             bytes, or None to indicate the end of an utterance
        shutdown_event: event used to signal shutdown across threads
    """

    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    aggressiveness = 3
    vad = webrtcvad.Vad(aggressiveness)

    padding_ms = 300
    ratio = 0.75
    frame_duration_ms = 1000 * CHUNK // SAMPLE_RATE
    num_padding_frames = padding_ms // frame_duration_ms
    # buffer that allows us to include padding_ms prior to being triggered in
    # the frames that get put on the audio_frames_q
    ring_buffer = collections.deque(maxlen=num_padding_frames)

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
                rate=SAMPLE_RATE,
                frames_per_buffer=CHUNK,
                input=True)
            
            # Initialize array to store frames. 
            frames: bytes = []
            # true if VAD has determined that we're speaking
            triggered = False
            
            # Audio ON loop:
            # - continually collect audio
            # - when we've found speech, put that on the audio_frames_q
            # - break when audio_ctrl gets unset or we get the shutdown signal
            # start = time.time()
            while audio_ctrl.is_set() and not shutdown_event.is_set():
                # read a frame
                frame: bytes = stream.read(CHUNK)
                # voice activity detection
                is_speech = vad.is_speech(frame, SAMPLE_RATE)
                # if VAD hasn't found speech yet
                if not triggered:
                    ring_buffer.append((frame, is_speech))
                    num_voiced = len([f for f, speech in ring_buffer if speech])
                    if num_voiced > ratio * ring_buffer.maxlen:
                        triggered = True
                        for f, s in ring_buffer:
                            audio_frames_q.put(f)
                        ring_buffer.clear()
                # but if we have...
                else:
                    audio_frames_q.put(frame)
                    ring_buffer.append((frame, is_speech))
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                    # end of the line for this utterance
                    if num_unvoiced > ratio * ring_buffer.maxlen:
                        triggered = False
                        audio_frames_q.put(None)
                        ring_buffer.clear()

            # throw out a None to end the utterance for any consumers down the
            # line (in case we stopped in the middle of an utterance)
            audio_frames_q.put(None)
            # end = time.time()

            # Stop and close the stream 
            stream.stop_stream()
            stream.close()

            logger.info('Finished recording')

        # 40 msec seems like a good wait time
        time.sleep(0.040)

    # Terminate the PortAudio interface
    p.terminate()

def read_audio_from_file(audio_file: str) -> bytes:
    """Reads audio from a .wav file
    
    From deepspeech/client.py

    Args:
        audio_file: path to the audio file
    
    Returns:
        [description]
        bytes
    
    Raises:
        Error: [description]
    """
    fin = wave.open(audio_file, 'rb')
    SAMPLE_RATE = fin.getframerate()
    if SAMPLE_RATE != 16000:
        raise Exception('Warning: original sample rate ({}) is different than 16kHz.'
            'Resampling might produce erratic speech recognition.'.format(SAMPLE_RATE))
    else:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
        audio_length = fin.getnframes() * (1/16000)
        fin.close()
        return audio, audio_length
