""" Contains the speech to text inference engine backend that converts raw input
audio to a stream of decoded output for subsequent parsing
"""

import logging
import time
import yaml

import numpy as np
from nptyping import Array

from deepspeech import Model, Stream

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class STTEngine:
    pass

class DeepSpeechEngine(STTEngine):
    """Based on Mozilla's DeepSpeech project

    This code adapted from deepspeech/client.py

    For context on the
    model and scorer, see:
    https://deepspeech.readthedocs.io/en/latest/USING.html

    For API docs see:
    https://deepspeech.readthedocs.io/en/latest/Python-API.html#model

    Assumes 16 kHz mono audio input
    """

    def __init__(self, config_file: str):
        """init
        
        Args:
            config_file: path to the YAML config file
        """
        super(DeepSpeechEngine, self).__init__()

        with open(config_file, 'r') as f:
            config = yaml.load(f)
        # load the 
        logger.debug('Loading model from file {}'.format(config['model']))
        model_load_start = time.time()
        self._model = Model(config['model'])
        self._model.enableExternalScorer(config['scorer'])
        model_load_end = time.time() - model_load_start
        logger.debug('Loaded model in {:.3}s.'.format(model_load_end))

        # for holding a stream
        self._streaming = False
        self._stream_context: Stream = None

    def transform(self, audio: Array[np.int16], fs: int) -> str:
        """ Transform audio to text
        
        Args:
            audio: array of int16s representing the audio frames
            fs: frames per second
        
        Returns:
            The text output
        """
        return self._model.stt(audio, fs)

    def new_stream(self):
        """Create a new stream to which to feed audio frames continuously for inference        
        """
        self._stream_context = self._model.createStream()
        self._streaming = True

    def feed_stream(self, frame: Array[np.int16]):
        """Feed audio frame to the stream
        
        Args:
            frame: audio frame
        """
        assert self._streaming
        assert frame is not None
        self._stream_context.feedAudioContent(
            np.frombuffer(frame, np.int16))

    def end_stream(self) -> str:
        """Finish the stream and return the infered content
        
        Returns:
            the text output
        """
        if self._streaming:
            return self._stream_context.finishStream()
        else:
            return None
