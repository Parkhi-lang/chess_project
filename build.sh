#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# Download Linux Stockfish binary
mkdir -p stockfish_linux
curl -L https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-avx2.tar -o sf.tar
tar -xf sf.tar -C stockfish_linux
chmod +x stockfish_linux/stockfish/stockfish-ubuntu-x86-64-avx2

python manage.py collectstatic --noinput
python manage.py migrate
