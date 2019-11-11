""" Main script for the dictation tool
"""

import logging
import time

import click 
import numpy as np
import pyaudio
import wave

from input_engine import DeepSpeechEngine

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def read_audio_from_file(audio_file: str) -> np.array:
    """From deepspeech/client.py    
    """
    fin = wave.open(audio_file, 'rb')
    fs = fin.getframerate()
    if fs != 16000:
        raise Error('Warning: original sample rate ({}) is different than 16kHz.'
            'Resampling might produce erratic speech recognition.'.format(fs))
    else:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
        audio_length = fin.getnframes() * (1/16000)
        fin.close()
        return audio, audio_length

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

    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    fs = 16000   # Record at 16k samples per second
    seconds = 3
    filename = "output.wav"


    engine = DeepSpeechEngine('config_deepspeech.yaml')

    # if we're just doing speech to text on an input audio file
    if audio_file is not None:
        audio, audio_length = read_audio_from_file(audio_file)

        start = time.time()
        text = engine.transform(audio, fs)
        print(text)
        end = time.time()
        print(f"Took {end - start:.2f}s for stt on {audio_length:.2f}s input")
        return


    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    print('Recording')

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    # Store data in chunks for 3 seconds
    for i in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream 
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()

    print('Finished recording')

    start = time.time()
    # text = engine.transform(frames, fs)
    frames = np.frombuffer(b''.join(frames), np.int16)
    out = engine._model.stt(frames, fs)
    print(out)
    end = time.time()
    print(f"Took {end - start} seconds")

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