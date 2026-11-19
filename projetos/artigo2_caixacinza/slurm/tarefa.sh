#!/bin/bash
# Uma tarefa = uma linha de tarefas/<bloco>.txt. Recebe o bloco em $BLOCO (definido por submeter.sh).
#SBATCH --job-name=a2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x_%A_%a.out
export NTHREADS=${SLURM_CPUS_PER_TASK:-4}
export OMP_NUM_THREADS=$NTHREADS MKL_NUM_THREADS=$NTHREADS OPENBLAS_NUM_THREADS=$NTHREADS
source "${VENV:-$HOME/venv_artigo2}/bin/activate"
cd "${SLURM_SUBMIT_DIR}"
LINHA=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" tarefas/${BLOCO}.txt)
SAIDA=$(echo "$LINHA" | sed -E 's/.*--saida ([^ ]+).*/\1/')
if [ -f "$SAIDA/resultado.json" ]; then echo "ja feito: $SAIDA"; exit 0; fi   # permite ressubmeter
mkdir -p "$SAIDA"; echo "[$(hostname)] $(date) $LINHA"
lscpu 2>/dev/null | grep -E 'Model name|^CPU\(s\)' > "$SAIDA/maquina.txt"; cat "$SAIDA/maquina.txt"
if [ -x /usr/bin/time ]; then /usr/bin/time -v -o "$SAIDA/tempo.txt" python codigo/roda.py $LINHA; else python codigo/roda.py $LINHA; fi
