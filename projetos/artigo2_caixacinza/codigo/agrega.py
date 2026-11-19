"""Junta os resultado.json de resultados/<bloco>/<cancer>__<tag>/ em tabelas e figuras.
Uso: python codigo/agrega.py [pasta_resultados]   -> resultados/resumo.md, todos.csv, cenarios.csv, figuras_resumo/"""
import os, sys, json, glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resultados')
FIG = os.path.join(RES, 'figuras_resumo'); os.makedirs(FIG, exist_ok=True)
lin, cen = [], []
def le(f, bloco, tag, cancer):
    r = json.load(open(f)); a = r['args']
    x = dict(bloco=bloco, cancer=cancer, tag=tag, modelo='global_' + a.get('hosp_global', '') if a['cancer'] == 'global' else 'separado',
             espera=a.get('espera', 'comum'), vigil=a.get('vigil'), fase=a.get('fase'), W=a['W'], L=a['L'], semente=a['semente'], boot=a['boot'],
             divisao=a['divisao'], corte=a['corte'], ablacao=a['ablacao'], nivel=a['nivel'], origem=a['origem'],
             D=r['meta']['D'], n_teste=r['n']['teste'], nll_teste=r['nll_teste'], C=r['cindex']['caixa_cinza'],
             C_EC=r['cindex']['so_EC'], C_ML=r['cindex'].get('ml', np.nan), ECE=r['ECE_S60'], tempo_min=r['tempo_s'] / 60,
             cpu=r.get('maquina', {}).get('cpu', ''))
    for s in r['S60']: x[f'vies_S60_EC{s["EC"]}'] = 100 * (s['modelo'] - s['KM_teste'])
    for k in ('O', 'V', 'Rad'): x[f'WAPE_{k}'] = 100 * r['wape'][k]['total']
    ch = r.get('calib_hospital', {}).get('teste', {})
    x['OE_teste'] = ch.get('OE_total', np.nan); x['hosp_fora_IC95'] = ch.get('fora_IC95', np.nan)
    ip = r.get('ipw_cacon', {}); x['CACON_IPW'] = ip.get('S60_diferenca_IPW', np.nan); x['CACON_modelo'] = ip.get('S60_diferenca_modelo', np.nan)
    tr = r.get('placebo_troca_hospital_mesmo_tipo', {}).get('d_obitos_pct', []); x['troca_mesmo_tipo_max'] = max(map(abs, tr)) if tr else np.nan
    for k, v in r.get('wape_teste', {}).items(): x[f'WAPE_fora_{k}'] = 100 * v
    tt = r.get('totais_teste', {})
    if tt: x['obitos_fora_erro_pct'] = 100 * (tt['obitos_2015_22_mod'] / max(tt['obitos_2015_22_obs'], 1) - 1)
    if 'covid' in r: x['covid_excesso_pct'] = 100 * (r['covid']['obs'] / r['covid']['mod'] - 1)
    lin.append(x)
    if 'cenarios' in r:
        base = r['cenarios'][0]
        for c in r['cenarios'][1:]:
            cen.append(dict(bloco=bloco, cancer=cancer, tag=tag, W=a['W'], L=a['L'], ablacao=a['ablacao'], cenario=c['cenario'],
                            d_obitos_pct=100 * (c['obitos_2015_22'] / base['obitos_2015_22'] - 1), d_obitos=c['obitos_2015_22'] - base['obitos_2015_22'],
                            d_S60_pp=100 * (c['S60_total'] - base['S60_total']), d_vivos_pct=100 * (c['vivos_dez22'] / base['vivos_dez22'] - 1),
                            d_remissao_pct=100 * (c['remissao_adm_dez22'] / base['remissao_adm_dez22'] - 1),
                            obitos_evitados_por_100=(-(c['obitos_2015_22'] - base['obitos_2015_22']) / c['n_antecipados'] * 100) if c.get('n_antecipados') else np.nan))
for f in sorted(glob.glob(os.path.join(RES, '*', '*', 'resultado.json'))):          # modelos separados
    bloco = os.path.basename(os.path.dirname(os.path.dirname(f)))
    if bloco == 'teste': continue
    le(f, bloco, os.path.basename(os.path.dirname(f)).split('__')[-1], json.load(open(f))['args']['cancer'])
for f in sorted(glob.glob(os.path.join(RES, '*', '*', '*', 'resultado.json'))):     # modelo global: <bloco>/global__<tag>/<cancer>/
    p = f.split(os.sep); bloco, tag, cancer = p[-4], p[-3].split('__')[-1], p[-2]
    if bloco != 'teste': le(f, bloco, tag, cancer)
T = pd.DataFrame(lin); C = pd.DataFrame(cen)
T.to_csv(os.path.join(RES, 'todos.csv'), index=False); C.to_csv(os.path.join(RES, 'cenarios.csv'), index=False)
md = ['# Resumo dos testes do Artigo 2', '', f'{len(T)} rodadas concluídas, {T.cancer.nunique() if len(T) else 0} cânceres.', '',
      'C = C-index no teste (risco = 1 − S(60)); ECE = erro médio de calibração de S(60) por decis (pontos de 0 a 1);',
      'viés S60 = modelo − KM do teste, em p.p.; WAPE em % (O óbitos, V vivos acompanhados, Rad remissão administrativa).', '']
met = ['C', 'C_EC', 'C_ML', 'ECE', 'vies_S60_EC1', 'vies_S60_EC2', 'vies_S60_EC3', 'vies_S60_EC4', 'WAPE_O', 'WAPE_V', 'WAPE_Rad', 'tempo_min']
def tab(df, idx, cols, tit, fmt='{:.3f}'):
    if not len(df): return
    md.extend([f'## {tit}', '', df.groupby(idx)[cols].agg(lambda v: v.mean()).round(3).to_markdown(), ''])
def ms(v):
    v = v.dropna(); return f'{v.mean():.3f} ± {v.std():.3f}' if len(v) > 1 else (f'{v.mean():.3f}' if len(v) else '')
if len(T):
    tab(T[T.bloco == 'b1_base'], 'cancer', met, 'Rodada base (W = 0,1; L = 1,2)')
    s = T[T.bloco == 'b2_sementes']
    if len(s):
        md.extend(['## Variação entre sementes (média ± desvio, 10 divisões e inicializações)', '',
                   s.groupby(['cancer', 'W'])[['C', 'ECE', 'WAPE_O', 'WAPE_V', 'WAPE_Rad']].agg(ms).to_markdown(), ''])
    g = T[T.bloco == 'b3_grade']
    if len(g):
        for m in ('C', 'WAPE_O', 'WAPE_Rad', 'ECE'):
            md.extend([f'## Grade W × L: {m}', '', g.pivot_table(index=['cancer', 'W'], columns='L', values=m).round(3).to_markdown(), ''])
        cs = sorted(g.cancer.unique()); fig, ax = plt.subplots(2, len(cs), figsize=(4 * len(cs), 6.5), squeeze=False)
        for j, c in enumerate(cs):
            for i, m in enumerate(('C', 'WAPE_O')):
                pv = g[g.cancer == c].pivot_table(index='W', columns='L', values=m)
                im = ax[i, j].imshow(pv.values, cmap='viridis' if m == 'C' else 'viridis_r', aspect='auto')
                ax[i, j].set_xticks(range(len(pv.columns)), pv.columns); ax[i, j].set_yticks(range(len(pv.index)), pv.index)
                for (u, v), val in np.ndenumerate(pv.values): ax[i, j].text(v, u, f'{val:.3f}' if m == 'C' else f'{val:.0f}', ha='center', va='center', color='w', fontsize=8)
                ax[i, j].set_title(f'{c}: {m}'); ax[i, j].set_xlabel('L'); ax[i, j].set_ylabel('W')
        plt.tight_layout(); plt.savefig(os.path.join(FIG, 'grade_W_L.png'), dpi=150); plt.close()
    tab(T[T.bloco == 'b4_temporal'], ['cancer', 'corte', 'W'], ['C', 'C_EC', 'ECE', 'vies_S60_EC1', 'vies_S60_EC4', 'WAPE_O'], 'Validação temporal (treino: coortes antes do corte; teste: a partir do corte)')
    tab(T[T.bloco.isin(['b5_ablacao', 'b1_base'])], ['cancer', 'tag'], ['C', 'ECE', 'WAPE_O', 'WAPE_V', 'WAPE_Rad'], 'Ablações (comparar com W0.1 = modelo completo)')
    b = T[T.bloco == 'b6_bootstrap']
    if len(b):
        q = lambda v: f'{v.quantile(.025):.3f} a {v.quantile(.975):.3f}'
        md.extend(['## Bootstrap de pacientes (intervalo de 95%)', '', b.groupby('cancer')[['C', 'ECE', 'WAPE_O', 'WAPE_Rad']].agg(q).to_markdown(), ''])
if len(T):
    v = T[T.bloco.isin(['b1_base', 'b2_sementes', 'b6_bootstrap'])]
    md.extend(['## Confiabilidade sem novo treino (média entre rodadas)', '', 'OE_teste: óbitos observados/esperados até 60 meses no teste; hosp_fora_IC95: fração de hospitais fora do IC de 95% de Poisson (esperado 0,05);',
               'CACON_IPW x CACON_modelo: diferença de S(60) entre CACON e os demais, estimada por ponderação pelo escore de propensão e pelo cenário do modelo;',
               'troca_mesmo_tipo_max: maior variação dos óbitos (%) ao trocar o hospital de cada paciente por outro do mesmo tipo (esperado perto de 0).', '',
               v.groupby('cancer')[['OE_teste', 'hosp_fora_IC95', 'CACON_IPW', 'CACON_modelo', 'troca_mesmo_tipo_max']].mean().round(3).to_markdown(), ''])
    r8 = T[T.bloco == 'b8_regiao']
    if len(r8):
        md.extend(['## Região deixada de fora (uma DRS por rodada)', '', r8.groupby('cancer')[['C', 'OE_teste', 'WAPE_fora_O', 'WAPE_fora_V', 'WAPE_fora_Rad', 'obitos_fora_erro_pct']].describe().round(2).T.to_markdown(), ''])
    t4 = T[T.bloco == 'b4_temporal']
    if len(t4) and 'WAPE_fora_O' in t4:
        md.extend(['## Previsão para a frente (coortes a partir do corte)', '', t4.groupby(['cancer', 'corte', 'W'])[[c for c in ['C', 'WAPE_fora_O', 'WAPE_fora_V', 'obitos_fora_erro_pct', 'covid_excesso_pct'] if c in t4]].mean().round(2).to_markdown(), ''])
if len(C):
    cp = C[C.bloco == 'b7_placebo']
    if len(cp):
        md.extend(['## Placebo: hospital e tipo embaralhados entre pacientes (efeitos de hospital deveriam sumir)', '', cp.groupby(['cancer', 'cenario'])['d_obitos_pct'].agg(['mean', 'min', 'max']).round(2).to_markdown(), ''])
    cb = C[C.bloco == 'b6_bootstrap']
    if len(cb):
        q = lambda v: f'{v.median():.2f} [{v.quantile(.025):.2f}; {v.quantile(.975):.2f}]'
        md.extend(['## Cenários: efeito com intervalo de 95% do bootstrap', '', 'Δ óbitos 2015–2022 (%), Δ S(60) (p.p.), óbitos evitados por 100 pacientes antecipados.', '',
                   cb.groupby(['cancer', 'cenario'])[['d_obitos_pct', 'd_S60_pp', 'd_remissao_pct', 'obitos_evitados_por_100']].agg(q).to_markdown(), ''])
        cs = sorted(cb.cancer.unique()); ns = sorted(cb.cenario.unique())
        fig, ax = plt.subplots(1, len(cs), figsize=(5 * len(cs), 4.2), sharey=True, squeeze=False)
        for j, c in enumerate(cs):
            dd = [cb[(cb.cancer == c) & (cb.cenario == n)].d_obitos_pct.values for n in ns]
            ax[0, j].boxplot(dd, vert=False); ax[0, j].set_yticks(range(1, len(ns) + 1), ns, fontsize=7); ax[0, j].axvline(0, color='k', lw=.8)
            ax[0, j].set_title(c); ax[0, j].set_xlabel('Δ óbitos 2015–2022 (%)')
        plt.tight_layout(); plt.savefig(os.path.join(FIG, 'cenarios_bootstrap.png'), dpi=150); plt.close()
    ca = C[C.bloco.isin(['b5_ablacao', 'b1_base'])]
    if len(ca):
        md.extend(['## Cenários sob ablação (Δ óbitos 2015–2022, %)', '', ca.pivot_table(index=['cancer', 'cenario'], columns='tag', values='d_obitos_pct').round(2).to_markdown(), ''])
    cg = C[C.bloco == 'b3_grade']
    if len(cg):
        md.extend(['## Cenários ao longo da grade W × L (Δ óbitos 2015–2022, %)', '', cg.pivot_table(index=['cancer', 'cenario'], columns='tag', values='d_obitos_pct').round(2).to_markdown(), ''])
if len(T) and (T.bloco == 'b9_global').any():
    cmp_ = T[T.bloco.isin(['b1_base', 'b2_sementes', 'b9_global']) & (T.W == 0.1) & (T.ablacao == 'completo')]
    md.extend(['## Modelo global (5 cânceres, o câncer como seletor) x modelos separados', '',
               'Mesmas sementes => mesmos pacientes de teste em cada câncer. separado = b1_base e b2_sementes (W = 0,1);',
               'global_compartilhado = um efeito por hospital em todos os cânceres; global_por_cancer = um por (câncer, hospital).', '',
               cmp_.groupby(['cancer', 'modelo'])[['nll_teste', 'C', 'ECE', 'vies_S60_EC1', 'vies_S60_EC2', 'vies_S60_EC3', 'vies_S60_EC4',
                                                   'WAPE_O', 'WAPE_V', 'hosp_fora_IC95', 'troca_mesmo_tipo_max']].agg(ms).to_markdown(), ''])
    e10 = T[T.bloco == 'b10_estados']
    if len(e10):
        md.extend(['## Estados novos: espera por coorte, fase inicial do tratamento, vigilância', '',
                   e10.groupby(['cancer', 'tag'])[['nll_teste', 'C', 'ECE', 'vies_S60_EC1', 'vies_S60_EC2', 'vies_S60_EC3', 'vies_S60_EC4', 'WAPE_O', 'WAPE_V', 'hosp_fora_IC95']].mean().round(3).to_markdown(), ''])
if len(T):
    md.extend(['## Máquina e tempo', '', T.groupby(['cancer', 'cpu'])['tempo_min'].describe()[['count', 'mean', 'max']].round(1).to_markdown(), ''])
open(os.path.join(RES, 'resumo.md'), 'w').write('\n'.join(md))
print('\n'.join(md[:60]))
