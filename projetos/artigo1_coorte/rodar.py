"""Ponto de entrada para o cluster. Exemplos:
  python rodar.py ajuste     --cancer colo
  python rodar.py bootstrap  --cancer colo --inicio 0 --n 20
  python rodar.py vies       --cancer colo --cenario realista --inicio 0 --n 10
  python rodar.py cobertura  --cancer colo --serie 7
  python rodar.py validacao  --cancer colo --janela 60
Versao da censura: --censura entrada (A, censura como entrada) ou --censura ar (B, censura estimada);
o padrao vem da variavel de ambiente CENSURA. Os resultados vao para resultados/ com o sufixo da versao."""
import argparse, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coorte as K

ap = argparse.ArgumentParser()
ap.add_argument('etapa', choices=['ajuste', 'bootstrap', 'vies', 'cobertura', 'validacao'])
ap.add_argument('--cancer', required=True, choices=list(K.CANCERES))
ap.add_argument('--dados', default=os.environ.get('DADOS', 'dados'))
ap.add_argument('--saida', default='resultados')
ap.add_argument('--inicio', type=int, default=0)
ap.add_argument('--n', type=int, default=200)
ap.add_argument('--cenario', default=None)
ap.add_argument('--serie', type=int, default=0)
ap.add_argument('--janela', type=int, default=None)
ap.add_argument('--censura', default=os.environ.get('CENSURA', 'entrada'), choices=['entrada', 'ar'])
ap.add_argument('--remissao', default=os.environ.get('REMISSAO', 'Q'), choices=['Q', 'S'])
a = ap.parse_args()
os.makedirs(a.saida, exist_ok=True)
SUF = '' if a.remissao == 'Q' else '_remS'
dd = K.Dados(a.cancer, a.dados, a.censura, a.remissao); t0 = time.time()
arq_aj = os.path.join(a.saida, f'ajuste_{a.cancer}_{a.censura}{SUF}.json')

if a.etapa == 'ajuste':
    K.recupera_sobrevida(dd)
    th, c = K.estima(dd, partidas=6)
    json.dump(dict(cancer=a.cancer, censura=a.censura, theta=th.tolist(), custo=c, nomes=K.nomes(a.censura), phi=dd.phi.tolist()), open(arq_aj, 'w'), indent=1)
else:
    aj = json.load(open(arq_aj)); th0 = np.array(aj['theta']); dd.phi = np.array(aj.get('phi', [0, 0, 0, 0]))
    if a.etapa == 'bootstrap':
        K.bootstrap(dd, th0, B=a.n, inicio_rep=a.inicio, arquivo=os.path.join(a.saida, f'boot_{a.cancer}_{a.censura}{SUF}_{a.inicio:04d}.jsonl'))
    elif a.etapa == 'vies':
        K.simulacao_vies(dd, th0, n_series=a.n if a.n != 200 else 50, cenario=a.cenario, inicio=a.inicio,
                         arquivo=os.path.join(a.saida, f'vies_{a.cancer}_{a.censura}{SUF}_{a.cenario}_{a.inicio:03d}.jsonl'))
    elif a.etapa == 'cobertura':
        K.simulacao_cobertura(dd, th0, series=[a.serie], B=50, arquivo=os.path.join(a.saida, f'cob_{a.cancer}_{a.censura}{SUF}_{a.serie:02d}.jsonl'))
    elif a.etapa == 'validacao':
        jan = (a.janela,) if a.janela else (24, 36, 60, 96, 120)
        K.validacao(dd, janelas=jan, arquivo=os.path.join(a.saida, f'val_{a.cancer}_{a.censura}{SUF}_W{a.janela or 0:03d}.jsonl'))
print(a.etapa, a.cancer, a.censura, 'remissao', a.remissao, 'concluido em %.0f s' % (time.time() - t0))
