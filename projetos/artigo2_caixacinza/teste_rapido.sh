#!/bin/bash
# Confere a instalacao e os dados em poucos minutos (1 epoca por etapa), sem SLURM.
# So testa os canceres cuja pasta em dados/ tem o <cancer>_v2.csv.
source "${VENV:-$HOME/venv_artigo2}/bin/activate"
for c in $(ls dados); do
  if ! ls dados/$c | grep -qi "_v2.csv"; then echo "pulando $c (sem ${c}_v2.csv)"; continue; fi
  python codigo/roda.py --cancer $c --saida resultados/teste/$c --epA 1 --epB 1 --figuras 1 || echo "FALHOU: $c"
done
# modelo global numa amostra de 5% de cada cancer (1 epoca por etapa)
python codigo/roda.py --cancer global --frac 0.05 --saida resultados/teste/global --epA 1 --epB 1 --cenarios 0 || echo "FALHOU: global"
grep -h "\[dados\]\|\[fim\]\|\[fim global\]" resultados/teste/*/log.txt
