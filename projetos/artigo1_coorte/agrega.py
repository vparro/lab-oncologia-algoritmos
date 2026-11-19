"""Resume os resultados de resultados/ em tabelas (resumo.md e CSVs), por versao da censura e lado a lado."""
import glob, json, os, numpy as np, pandas as pd, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import coorte as K
R = 'resultados'
def ler(padrao):
    out = []
    for f in sorted(glob.glob(os.path.join(R, padrao))):
        if '_remS' in os.path.basename(f) and '_remS' not in padrao: continue   # nao misturar as regras da remissao
        for l in open(f):
            try: out.append(json.loads(l))
            except Exception: pass
    return out
def tab(d, index=True): return '```\n' + d.to_string(index=index) + '\n```'
md = ['# Resumo dos resultados do cluster', '']
VROT = {'entrada': 'Versão A: censura como entrada', 'ar': 'Versão B: censura estimada (AR)',
        'entrada_remS': 'Versão A, remissão S(D): censura como entrada, toda a massa viva passa a R em D',
        'ar_remS': 'Versão B, remissão S(D): censura estimada, toda a massa viva passa a R em D'}
for V in VROT:
    if not glob.glob(os.path.join(R, f'ajuste_*_{V}.json')): continue
    md += [f'# {VROT[V]}', '']
    # bootstrap
    rows = []
    for c in K.CANCERES:
        B = ler(f'boot_{c}_{V}_*.jsonl')
        if not B: continue
        th0 = json.load(open(os.path.join(R, f'ajuste_{c}_{V}.json')))['theta']
        S = np.array([b['S'] for b in B]); T = np.array([b['theta'] for b in B])
        for i in range(4):
            for k, t in ((1, 12), (4, 60), (5, 120)):
                lo, md_, hi = np.percentile(S[:, i, k], [2.5, 50, 97.5]); rows.append([c, f'EC{i+1}', f'S{t}', md_, lo, hi, len(B)])
        for j, n in enumerate(K.nomes(V.split('_')[0])):
            lo, hi = np.percentile(T[:, j], [2.5, 97.5]); rows.append([c, '', n, th0[j], lo, hi, len(B)])
    if rows:
        d = pd.DataFrame(rows, columns=['cancer', 'EC', 'grandeza', 'estimativa', 'IC2.5', 'IC97.5', 'replicas']); d.to_csv(f'bootstrap_{V}.csv', index=False)
        md += ['## Bootstrap', tab(d.round(4), False), '']
    # vies
    rows = []
    for c in K.CANCERES:
        for r in ler(f'vies_{c}_{V}_*.jsonl'):
            for i in range(4):
                rows.append([c, r['cen'], f'EC{i+1}', r['true_s']['S'][i][1], r['est_s']['S'][i][1]] + [r['true'][j] for j in range(3)] + [r['est'][j] for j in range(3)])
    if rows:
        d = pd.DataFrame(rows, columns=['cancer', 'cenario', 'EC', 'S60_v', 'S60_e', 'p1_v', 'p2_v', 'p3_v', 'p1_e', 'p2_e', 'p3_e'])
        g = d.groupby(['cancer', 'cenario', 'EC']).apply(lambda x: pd.Series({'vies_S60': (x.S60_e - x.S60_v).mean(), 'rmse_S60': np.sqrt(((x.S60_e - x.S60_v) ** 2).mean()), 'n': len(x)}))
        p = d[d.EC == 'EC1'].groupby(['cancer', 'cenario']).apply(lambda x: pd.Series({f'p{j}_mediana': x[f'p{j}_e'].median() for j in (1, 2, 3)} | {'p_verdadeiro': x.p1_v.iloc[0]}))
        g.to_csv(f'simulacao_vies_{V}.csv'); p.to_csv(f'simulacao_progressao_{V}.csv')
        md += ['## Simulação: viés de S(60)', tab(g.round(4)), '', '## Simulação: progressão estimada (% ao mês = x100)', tab(p.round(4)), '']
    # cobertura
    rows = []
    for c in K.CANCERES:
        C = ler(f'cob_{c}_{V}_*.jsonl')
        for i in range(4):
            hit = [np.percentile([b['est_s']['S'][i][1] for b in r['boot']], 2.5) <= r['true_s']['S'][i][1] <= np.percentile([b['est_s']['S'][i][1] for b in r['boot']], 97.5) for r in C]
            if hit: rows.append([c, f'EC{i+1}', 'S60', np.mean(hit), len(hit)])
    if rows:
        d = pd.DataFrame(rows, columns=['cancer', 'EC', 'grandeza', 'cobertura', 'series']); d.to_csv(f'cobertura_{V}.csv', index=False)
        md += ['## Cobertura dos IC 95% (nominal 0,95)', tab(d.round(3), False), '']
    # validacao
    rows = []
    for c in K.CANCERES:
        for r in ler(f'val_{c}_{V}_W*.jsonl'):
            for h, e in r['err'].items():
                rows.append([c, r['W'], int(h), e['Otot'], r['base'][h]['pers_tot'], r['base'][h]['dec_tot'],
                             np.mean([e[f'A{i}'] for i in range(1, 5)]), np.mean([e[f'R{i}'] for i in range(1, 5)]), np.mean([e[f'C{i}'] for i in range(1, 5)]) if f'C1' in e else np.nan])
    if rows:
        d = pd.DataFrame(rows, columns=['cancer', 'janela', 'horizonte', 'obitos_modelo', 'obitos_persist', 'obitos_deconv', 'tratamento', 'remissao', 'censurados'])
        g = d.groupby(['cancer', 'horizonte', 'janela']).median(); g.to_csv(f'validacao_{V}.csv')
        md += ['## Validação temporal (mediana do erro relativo)', tab(g.round(3)), '']

open('resumo.md', 'w').write('\n'.join(md)); print('resumo.md gravado')
