#!/bin/bash
# Cria o ambiente Python do usuario (sem privilegios). PyTorch so CPU.
set -e
python3 -m venv ${VENV:-$HOME/venv_artigo2}
source ${VENV:-$HOME/venv_artigo2}/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -c "import torch, pandas, openpyxl, matplotlib; print('ok, torch', torch.__version__)"
