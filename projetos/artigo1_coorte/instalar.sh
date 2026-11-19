#!/bin/bash
# Cria o ambiente Python (uma vez). Requer Python >= 3.10.
python3 -m venv "${VENV:-$HOME/venv_coorte}"
source "${VENV:-$HOME/venv_coorte}/bin/activate"
pip install --upgrade pip && pip install -r requirements.txt
python -c "import numpy, scipy, pandas, openpyxl; print('ambiente ok')"
