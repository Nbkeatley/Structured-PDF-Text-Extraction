#!/bin/bash

sudo apt update

sudo apt install -y tesseract-ocr libtesseract-dev

sudo apt install -y swig3.0
pip install jamspell

wget https://github.com/bakwc/JamSpell-models/raw/master/en.tar.gz -O en.tar.gz
tar -xvf en.tar.gz


