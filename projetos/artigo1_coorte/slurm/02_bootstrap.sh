#!/bin/bash
# 5 canceres x 25 blocos de 20 replicas = 500 replicas por cancer
#SBATCH --job-name=coorte_boot
#SBATCH --array=0-124
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%A_%a.out
source slurm/comum.sh
C=${CANCERES[$((SLURM_ARRAY_TASK_ID / 25))]}; INI=$(( (SLURM_ARRAY_TASK_ID % 25) * 20 ))
python rodar.py bootstrap --cancer $C --inicio $INI --n 20
