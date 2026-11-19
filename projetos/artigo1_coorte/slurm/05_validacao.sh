#!/bin/bash
# 5 canceres x 5 janelas = 25 tarefas
#SBATCH --job-name=coorte_val
#SBATCH --array=0-24
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%A_%a.out
source slurm/comum.sh
JAN=(24 36 60 96 120)
C=${CANCERES[$((SLURM_ARRAY_TASK_ID / 5))]}; WJ=${JAN[$((SLURM_ARRAY_TASK_ID % 5))]}
python rodar.py validacao --cancer $C --janela $WJ
