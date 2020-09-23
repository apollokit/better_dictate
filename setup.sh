#!/bin/bash

# see https://github.com/mozilla/DeepSpeech/releases/tag/v0.8.2

# install reqs for pyaudio
sudo apt install portaudio19-dev

# get the deepspeech language model
mkdir deepspeech-0.8.2-models
pushd deepspeech-0.8.2-models
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.8.2/deepspeech-0.8.2-models.pbmm
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.8.2/deepspeech-0.8.2-models.tflite
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.8.2/deepspeech-0.8.2-models.scorer
popd

./create_virtualenv.sh
