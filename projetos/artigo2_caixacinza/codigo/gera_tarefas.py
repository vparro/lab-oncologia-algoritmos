"""Gera as listas de tarefas (uma linha = argumentos de roda.py) para cada bloco de testes.
Uso: python codigo/gera_tarefas.py [canceres...]   (padrao: as pastas presentes em dados/)"""
import os, sys
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TODOS = ['colorretal', 'colo_utero', 'pulmao', 'mama', 'prostata']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dados import acha
pronto = lambda c: os.path.isdir(os.path.join(RAIZ, 'dados', c)) and acha(os.path.join(RAIZ, 'dados', c), f'{c}_v2.csv') is not None
can = sys.argv[1:] or [c for c in TODOS if pronto(c)]
falta = [c for c in TODOS if c not in can]
if falta: print('sem <cancer>_v2.csv em dados/ (fora desta rodada):', falta)
ANT = '--antecipa 0.1,0.2,0.5'
B = {}
def add(bloco, c, tag, args):
    B.setdefault(bloco, []).append(f'--cancer {c} --saida resultados/{bloco}/{c}__{tag} {args}')
for c in can:
    add('b1_base', c, 'W0.1', f'--W 0.1 --figuras 1 {ANT}')
    for s in range(10):
        for W in (0, 0.1):
            add('b2_sementes', c, f's{s}_W{W}', f'--W {W} --semente {3000+s} --cenarios {int(W>0)}')
    for W in (0, 0.03, 0.1, 0.3, 1, 3):
        for L in (0.6, 1.2, 2.0, 3.0):
            add('b3_grade', c, f'W{W}_L{L}', f'--W {W} --L {L} --cenarios 1')
    for corte in (2010, 2013, 2016, 2019):
        for W in (0, 0.1):
            add('b4_temporal', c, f'corte{corte}_W{W}', f'--W {W} --divisao temporal --corte {corte} --cenarios 0')
    for ab in ('sem_hosp', 'sem_reg', 'so_EC'):
        add('b5_ablacao', c, ab, f'--W 0.1 --ablacao {ab} {ANT}')
    for nv in (1, 2):
        add('b5_ablacao', c, f'nivel{nv}', f'--W 0.1 --nivel {nv} --cenarios 1')
    add('b5_ablacao', c, 'origem_diagnostico', f'--W 0.1 --origem diagnostico {ANT}')
    for pl in range(1, 6):
        add('b7_placebo', c, f'placebo{pl}', f'--W 0.1 --placebo {pl}')
    for r in range(17):
        add('b8_regiao', c, f'DRS{r:02d}', f'--W 0.1 --exclui_reg {r} --cenarios 0')
    for b in range(100):
        add('b6_bootstrap', c, f'boot{b:02d}', f'--W 0.1 --boot {b} {ANT}')
# b9: modelo global (todos os canceres presentes num modelo so; o cancer como seletor das taxas de base).
# compartilhado = um efeito por hospital em todos os canceres; por_cancer = referencia, equivale a efeitos separados.
# sementes 3000.. = as mesmas do b2 => mesmos pacientes de teste dos modelos separados.
if len(can) >= 2:
    lista = ','.join(can)
    for hg in ('compartilhado', 'por_cancer'):
        B.setdefault('b9_global', []).append(f'--cancer global --canceres {lista} --hosp_global {hg} --saida resultados/b9_global/global__{hg}_base --W 0.1 {ANT}')
        for s in range(5):
            B['b9_global'].append(f'--cancer global --canceres {lista} --hosp_global {hg} --saida resultados/b9_global/global__{hg}_s{s} --W 0.1 --semente {3000+s} --cenarios 1')
# b10: estados novos (18/11/2026) em cada cancer, com a mesma semente do b1_base
for c in can:
    add('b10_estados', c, 'espera_ec', f'--W 0.1 --espera ec {ANT}')
    add('b10_estados', c, 'espera_ec_LE3', f'--W 0.1 --espera ec --LE 3 {ANT}')
    add('b10_estados', c, 'fase', f'--W 0.1 --espera ec --fase 1 {ANT}')
    add('b10_estados', c, 'vigilancia', f'--W 0.1 --espera ec --vigil 1 {ANT}')
    add('b10_estados', c, 'vigilancia_fase', f'--W 0.1 --espera ec --vigil 1 --fase 1 {ANT}')
os.makedirs(os.path.join(RAIZ, 'tarefas'), exist_ok=True)
tot = 0
for k, v in B.items():
    open(os.path.join(RAIZ, 'tarefas', k + '.txt'), 'w').write('\n'.join(v) + '\n'); tot += len(v)
    print(f'{k:14s} {len(v):4d} tarefas')
print(f'total {tot} tarefas para {can}')
