#!/bin/bash
# 5 canceres x 5 cenarios x 5 blocos de 10 series = 125 tarefas (50 series por cenario)
#SBATCH --job-name=coorte_vies
#SBATCH --array=0-124
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%A_%a.out
source slurm/comum.sh
CEN=(realista p=0.0 p=0.005 p=0.01 p=0.02)
T=$SLURM_ARRAY_TASK_ID
C=${CANCERES[$((T / 25))]}; S=${CEN[$(( (T % 25) / 5 ))]}; INI=$(( (T % 5) * 10 ))
python rodar.py vies --cancer $C --cenario $S --inicio $INI --n 10
