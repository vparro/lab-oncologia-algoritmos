#!/bin/bash
# 5 canceres x 30 series; cada serie: 1 estimacao + bootstrap de 50 replicas
#SBATCH --job-name=coorte_cob
#SBATCH --array=0-149
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%A_%a.out
source slurm/comum.sh
C=${CANCERES[$((SLURM_ARRAY_TASK_ID / 30))]}; R=$((SLURM_ARRAY_TASK_ID % 30))
python rodar.py cobertura --cancer $C --serie $R
