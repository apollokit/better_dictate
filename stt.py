""" Contains the speech to text inference engine backend that converts raw input
audio to a stream of decoded output for subsequent parsing
"""

import logging
import time
import yaml
from typing import List

import numpy as np
from nptyping import Array

from deepspeech import Model

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class STTEngine:
    pass

class DeepSpeechEngine(STTEngine):
    """Based on Mozilla's DeepSpeech project

    This code largely stolen from deepspeech/client.py

    Assumes 16 kHz mono audio input
    """
    
    # These constants control the beam search decoder
    # Beam width used in the CTC decoder when building candidate transcriptions
    BEAM_WIDTH = 500
    # The alpha hyperparameter of the CTC decoder. Language Model weight
    LM_ALPHA = 0.75
    # The beta hyperparameter of the CTC decoder. Word insertion bonus.
    LM_BETA = 1.85

    # These constants are tied to the shape of the graph used (changing them changes
    # the geometry of the first layer), so make sure you use the same constants that
    # were used during training
    # Number of MFCC features to use
    N_FEATURES = 26
    # Size of the context window used for producing timesteps in the input vector
    N_CONTEXT = 9

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
        self._model = Model(config['model'], 
            DeepSpeechEngine.N_FEATURES, 
            DeepSpeechEngine.N_CONTEXT, 
            config['alphabet'], 
            DeepSpeechEngine.BEAM_WIDTH)
        self._model.enableDecoderWithLM(
            config['alphabet'], 
            config['lm'], 
            config['trie'], 
            DeepSpeechEngine.LM_ALPHA, 
            DeepSpeechEngine.LM_BETA)
        model_load_end = time.time() - model_load_start
        logger.debug('Loaded model in {:.3}s.'.format(model_load_end))

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
        self._stream_context = self._model.setupStream()

    def feed_stream(self, frame: Array[np.int16]):
        """Feed audio frame to the stream
        
        Args:
            frame: audio frame
        """
        self._model.feedAudioContent(
            self._stream_context, 
            np.frombuffer(frame, np.int16))

    def end_stream(self) -> str:
        """Finish the stream and return the infered content
        
        Returns:
            the text output
        """
        return self._model.finishStream(self._stream_context)