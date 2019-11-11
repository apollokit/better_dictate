#!/bin/bash

# see https://github.com/mozilla/DeepSpeech/releases/tag/v0.5.1 for more context

# install reqs for pyaudio
sudo apt install portaudio19-dev

# get the deepspeech language model
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.5.1/deepspeech-0.5.1-models.tar.gz
tar xvf deepspeech-0.5.1-models.tar.gz

./create_virtualenv.sh
