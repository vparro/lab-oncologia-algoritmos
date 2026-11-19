# Variaveis comuns. Ajuste a particao e o ambiente Python conforme o cluster.
# CENSURA (entrada ou ar) chega pelo submeter.sh; o padrao e entrada.
export CENSURA=${CENSURA:-entrada}
export REMISSAO=${REMISSAO:-Q}   # Q: original (so Q passa a R em D); S: toda a massa viva passa a R em D
CANCERES=(colo colo_utero mama prost pulm)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1   # 1 nucleo por tarefa
source "${VENV:-$HOME/venv_coorte}/bin/activate"
cd "${SLURM_SUBMIT_DIR}"
