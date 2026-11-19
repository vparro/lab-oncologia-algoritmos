#!/bin/bash
#SBATCH --job-name=coorte_ajuste
#SBATCH --array=0-4
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x_%A_%a.out
source slurm/comum.sh
python rodar.py ajuste --cancer ${CANCERES[$SLURM_ARRAY_TASK_ID]}
