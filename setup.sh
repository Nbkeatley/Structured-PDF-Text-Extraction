#!/bin/bash

sudo apt update

sudo apt install -y tesseract-ocr libtesseract-dev

pip install --upgrade pip==22.3.1 setuptools==65.6.3 wheel==0.38.4

pip install -r requirements.txt

# Download Spellcheck English-language dictionary for JamSpell
sudo apt install -y swig3.0
wget https://github.com/bakwc/JamSpell-models/raw/master/en.tar.gz -O en.tar.gz
tar -xvf en.tar.gz
