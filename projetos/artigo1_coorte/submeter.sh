#!/bin/bash
# Submete tudo para as 4 combinacoes: censura (entrada = A; ar = B) x regra da remissao (Q = original; S = variante).
# Em cada combinacao, as etapas 2 a 5 esperam o ajuste (etapa 1) daquela combinacao terminar.
# Exemplos:  bash submeter.sh                 (as 4)
#            VERSOES=entrada REMISSOES=S bash submeter.sh   (so a versao A com a remissao S)
set -e; mkdir -p logs resultados
VERSOES=${VERSOES:-entrada ar}; REMISSOES=${REMISSOES:-Q S}
for V in $VERSOES; do for M in $REMISSOES; do
  J1=$(sbatch --parsable --export=ALL,CENSURA=$V,REMISSAO=$M --job-name=coorte_ajuste_${V}_$M slurm/01_ajuste.sh)
  for s in 02_bootstrap 03_vies 04_cobertura 05_validacao; do
    sbatch --dependency=afterok:$J1 --export=ALL,CENSURA=$V,REMISSAO=$M --job-name=coorte_${s#0?_}_${V}_$M slurm/$s.sh
  done
  echo "censura $V, remissao $M: ajuste $J1 (demais etapas aguardando)"
done; done
