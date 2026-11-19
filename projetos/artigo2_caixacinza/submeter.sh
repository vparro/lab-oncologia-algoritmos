#!/bin/bash
# Submete os blocos de testes como job arrays. Uso:
#   bash submeter.sh                 # todos os blocos, na ordem de prioridade
#   bash submeter.sh b1_base b3_grade
# MAXSIM limita quantas tarefas de cada array rodam ao mesmo tempo (padrao 50).
set -e
mkdir -p logs resultados
python codigo/gera_tarefas.py          # regera a partir das pastas presentes em dados/
BLOCOS=${@:-b1_base b2_sementes b3_grade b4_temporal b5_ablacao b7_placebo b8_regiao b6_bootstrap b9_global b10_estados}
for b in $BLOCOS; do
  n=$(grep -c . tarefas/$b.txt)
  extra=""
  # modelo global: os 5 canceres num modelo so (cerca de 300 mil pacientes): mais nucleos, memoria e tempo
  if [ "$b" = "b9_global" ]; then extra="--cpus-per-task=8 --mem=24G --time=48:00:00"; fi
  id=$(sbatch --parsable $extra --export=ALL,BLOCO=$b --job-name=a2_$b --array=0-$((n-1))%${MAXSIM:-50} slurm/tarefa.sh)
  echo "$b: $n tarefas, job $id"
done
