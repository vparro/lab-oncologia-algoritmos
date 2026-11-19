"""Leitura dos dados de um cancer do RHC/SP (FOSP) para o modelo caixa-cinza.

Estrutura esperada (os nomes de pasta podem ter acento; a busca normaliza):
  dados/<cancer>/<cancer>_v2.csv           tabela por paciente (uma linha por paciente)
  dados/<cancer>/Predições/predicoes_ec{1..4}.xlsx   predicoes do ML do grupo (indice = linha do csv)
  dados/<cancer>/Kaplan-Meier/km_ec{1..4}.csv        KM dos dados (opcional)
  dados/<cancer>/<prefixo>_ec{1..4}.xlsx             series de coorte do Artigo 1 (opcional, so para conferencia)
cancer em {colorretal, colo_utero, pulmao, mama, prostata}.
"""
import os, unicodedata, json
import numpy as np, pandas as pd

PREFIXO = dict(colorretal='colo', colo_utero='colo_utero', pulmao='pulm', mama='mama', prostata='prost')
D_PADRAO = dict(colorretal=66, colo_utero=66, pulmao=66, mama=126, prostata=126)
MP = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
T_FIM_OBS = 288          # comparacoes de series ate dez/2023 (meses 0..287 desde jan/2000)

def _norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace(' ', '_')

def acha(raiz, nome):
    """Procura um arquivo pelo nome normalizado (sem acento, minusculo) abaixo de raiz."""
    alvo = _norm(nome)
    for dp, _, fs in os.walk(raiz, followlinks=True):
        for f in fs:
            if _norm(f) == alvo:
                return os.path.join(dp, f)
    return None

def acha_em(raiz, pasta, nome):
    alvo_p, alvo = _norm(pasta), _norm(nome)
    for dp, _, fs in os.walk(raiz, followlinks=True):
        if _norm(os.path.basename(dp)) == alvo_p:
            for f in fs:
                if _norm(f) == alvo:
                    return os.path.join(dp, f)
    return None

def mes(x):
    d = pd.to_datetime(x, errors='coerce')
    return (d.dt.year - 2000) * 12 + d.dt.month - 1

def detecta_D(d, raiz, cancer, log=print):
    """Regra administrativa da 'remissao' do registro: vivo e acompanhado ha >= D meses desde a
    consulta. Testa D em 54..140 contra a serie de remissao do Artigo 1, se ela existir."""
    c, u = mes(d.DTCONSULT).to_numpy(), mes(d.DTULTINFO).to_numpy(); ec = d.EC.to_numpy()
    S = {}
    for e in range(1, 5):
        f = acha(raiz, f'{PREFIXO[cancer]}_ec{e}.xlsx')
        if f is None: return D_PADRAO[cancer], None
        S[e] = pd.read_excel(f).remissao.to_numpy()
    err = {}
    for D in range(54, 141, 6):
        num = den = 0
        for e in range(1, 5):
            s = S[e]; T = np.arange(len(s)); m = ec == e
            R = ((c[m, None] + D <= T[None]) & (u[m, None] >= T[None])).sum(0)
            num += np.abs(R - s).sum(); den += s.sum()
        err[D] = num / max(den, 1)
    D0 = min(err, key=err.get)
    for D in range(D0 - 5, D0 + 6):
        num = den = 0
        for e in range(1, 5):
            s = S[e]; T = np.arange(len(s)); m = ec == e
            R = ((c[m, None] + D <= T[None]) & (u[m, None] >= T[None])).sum(0)
            num += np.abs(R - s).sum(); den += s.sum()
        err[D] = num / max(den, 1)
    Dm = min(err, key=err.get)
    log(f'[dados] regra da remissao: D={Dm} meses desde a consulta (erro relativo {err[Dm]:.4f}); padrao {D_PADRAO[cancer]}')
    return Dm, err[Dm]

def _predicoes(d, raiz, cancer, log=print):
    """Predicoes do ML do grupo, alinhadas as linhas do csv v2. Se o indice nao bater com o EC
    (caso do colo do utero, gerado sobre <cancer>.csv), alinha por chaves com aquele arquivo."""
    P = []
    for e in range(1, 5):
        f = acha_em(raiz, 'predicoes', f'predicoes_ec{e}.xlsx')
        if f is None:
            log('[dados] predicoes do ML nao encontradas: comparacao com o ML sera omitida'); return None
        p = pd.read_excel(f, index_col=0); p.columns = [int(c) for c in p.columns]; p['EC_p'] = e; P.append(p)
    P = pd.concat(P)
    ok = d.EC.reindex(P.index).to_numpy() == P.EC_p.to_numpy()
    if ok.mean() > 0.99 and not P.index.duplicated().any():
        return P.drop(columns='EC_p').reindex(d.index)
    f = acha(raiz, f'{cancer}.csv')
    if f is None:
        log('[dados] indice das predicoes nao bate com o csv v2 e nao ha <cancer>.csv: ML omitido'); return None
    o = pd.read_csv(f, low_memory=False); o['io'] = o.index
    k = ['INSTITU', 'IDADE', 'DTCONSULT', 'DTDIAG', 'DTULTINFO', 'ULTINFO', 'CEP', 'MORFO', 'TOPO']
    o = o.drop_duplicates(k, keep=False); dd = d[k].copy(); dd['iv'] = d.index
    m = dd.merge(o[k + ['io']], on=k, how='left').drop_duplicates('iv', keep=False).set_index('iv')
    io = m.io.reindex(d.index)
    log(f'[dados] predicoes alinhadas por chave com {os.path.basename(f)}: {io.notna().sum()} de {len(d)} pacientes')
    Q = P.drop(columns='EC_p'); Q = Q[~Q.index.duplicated()]
    out = Q.reindex(io.fillna(-1).astype(int).to_numpy()); out.index = d.index
    return out

def carrega(cancer, raiz, origem='consulta', D=None, log=print):
    """Retorna d (tabela), ev (eventos no tempo do modelo), cov (covariaveis), hosp, reg, S_ml, meta."""
    for nome in (cancer, PREFIXO[cancer]):                     # restringe a busca a pasta do cancer
        if os.path.isdir(os.path.join(raiz, nome)): raiz = os.path.join(raiz, nome); break
    f = acha(raiz, f'{cancer}_v2.csv')
    if f is None: raise FileNotFoundError(f'{cancer}_v2.csv nao encontrado abaixo de {raiz}')
    d = pd.read_csv(f, low_memory=False)
    d = d.drop(columns=[c for c in d.columns if c.startswith('Unnamed')])
    d['EC'] = d.ECGRUP.map(MP); n0 = len(d)
    d = d[d.EC.notna()].copy(); d['EC'] = d.EC.astype(int)
    col0 = 'DTCONSULT' if origem == 'consulta' else 'DTDIAG'
    d[col0] = d[col0].fillna(d.DTDIAG)
    if D is None: D, errD = detecta_D(d, raiz, cancer, log)
    else: errD = None
    S = _predicoes(d, raiz, cancer, log)
    keep = pd.to_datetime(d[col0]) < '2024-01-01'           # 2024-25: registro incompleto
    d = d[keep].copy(); S = S.loc[d.index] if S is not None else None
    ev = pd.DataFrame(index=d.index)
    ev['t_diag'] = mes(d[col0])                               # t0 = origem do paciente (mes calendario)
    tau = mes(d.DTULTINFO) - ev.t_diag; tt = mes(d.DTTRAT) - ev.t_diag; tr = mes(d.DTRECIDIVA) - ev.t_diag
    ev['ult'] = d.ULTINFO.values
    ev['d_obito'] = d.ULTINFO.isin([3, 4]).astype(int)
    ev['d_trat'] = tt.notna().astype(int)
    ev['t_trat'] = np.where(ev.d_trat == 1, tt.fillna(0).clip(lower=1), 0).astype(int)
    ev['d_rec'] = (tr.notna() & (ev.d_trat == 1)).astype(int)
    # recidiva so pode ocorrer depois de passar por Q: t_trat + 2 (com a fase inicial T, t_trat + 3)
    _piso_rec = 3 if __import__('os').environ.get('FASE', '0') == '1' else 2
    ev['t_rec'] = np.where(ev.d_rec == 1, np.maximum(tr.fillna(0), ev.t_trat + _piso_rec), 0).astype(int)
    tarde = (ev.d_rec == 1) & (ev.t_rec >= D)                 # recidiva apos D: fora do modelo (R absorvente)
    ev.loc[tarde, ['d_rec', 't_rec']] = 0
    piso = np.maximum(ev.t_trat, ev.t_rec)
    ev['tau'] = np.maximum(tau.fillna(0).astype(int), np.where(ev.d_obito == 1, piso + 1, piso)).clip(lower=1).astype(int)
    ev['EC'] = d.EC.values; ev['Dc'] = D
    c = pd.DataFrame(index=d.index)
    z = lambda x: (x - x.mean()) / (x.std() if x.std() > 0 else 1.0)
    c['idade'] = z(d.IDADE.astype(float))
    if d.SEXO.nunique() > 1: c['sexo_f'] = (d.SEXO == 2).astype(float)
    c['ano'] = z(pd.to_datetime(d[col0]).dt.year.astype(float))
    dist = np.log1p(d.DISTANCIA_CARRO); c['dist'] = z(dist.fillna(dist.median())); c['dist_na'] = d.DISTANCIA_CARRO.isna().astype(float)
    for v in ['ivs_infraestrutura_urbana', 'ivs_capital_humano', 'ivs_renda_e_trabalho']:
        if v in d: c[v] = z(d[v].fillna(d[v].median()))
    cat = [v for v in ['ESCOLARI', 'CATEATEND', 'DIAGPREV', 'HABILIT_HOSP', 'TOPOGRUP', 'EC'] if v in d and d[v].nunique() > 1]
    dm = pd.get_dummies(d[cat].astype(str), dtype=float, drop_first=True)
    c = pd.concat([c, dm], axis=1)
    hosp = d.INSTITU.astype('category').cat.codes.values; reg = d.DRS.astype('category').cat.codes.values
    meta = dict(cancer=cancer, prefixo=PREFIXO[cancer], D=int(D), erro_regra_remissao=errD, origem=origem,
                n_csv=n0, n_modelo=len(d), rec_apos_D=int(tarde.sum()),
                n_por_EC={int(e): int((d.EC == e).sum()) for e in range(1, 5)},
                ml_disponivel=S is not None and bool(S.notna().any().any()))
    log(f'[dados] {cancer}: {n0} no csv, {len(d)} no modelo (origem={origem}, D={D}); recidivas apos D descartadas: {int(tarde.sum())}')
    return d, ev, c, hosp, reg, S, meta

def series_observadas(ev, D, T=T_FIM_OBS):
    """Series do registro reconstruidas da tabela (validado contra as series do Artigo 1):
    O(t) obitos no mes; V(t) vivos acompanhados; Rad(t) 'remissao' administrativa = vivo,
    acompanhado e com t - t0 >= D."""
    t0 = ev.t_diag.to_numpy(); fim = t0 + ev.tau.to_numpy(); morto = ev.d_obito.to_numpy() == 1
    Tt = np.arange(T)
    O = np.bincount(fim[morto], minlength=T + 400)[:T].astype(float)
    ult = fim - morto
    V = ((t0[:, None] <= Tt[None]) & (ult[:, None] >= Tt[None])).sum(0).astype(float)
    Rad = ((t0[:, None] + D <= Tt[None]) & (ult[:, None] >= Tt[None])).sum(0).astype(float)
    return np.stack([O, V, Rad])

def carrega_global(canceres, raiz, origem='consulta', D=None, log=print, hosp_global='compartilhado', frac=1.0, semente=2026):
    """Modelo global: junta os canceres numa tabela so. O cancer entra como seletor: colunas CA_<cancer>
    (referencia = primeiro da lista) que deslocam as taxas de base, e interacoes EC_<e>_x_<cancer>.
    hosp_global: 'compartilhado' = o mesmo INSTITU tem um so efeito em todos os canceres;
                 'por_cancer'   = cada par (cancer, INSTITU) tem o seu (equivale aos modelos separados).
    frac < 1: amostra de pacientes de cada cancer (so para teste rapido)."""
    partes = []
    for k, c in enumerate(canceres):
        d, ev, cov, _, _, S, meta = carrega(c, raiz, origem, D, log)
        if frac < 1:
            sel = np.sort(np.random.default_rng(semente + k).choice(len(d), int(frac * len(d)), replace=False))
            d, ev, cov = d.iloc[sel], ev.iloc[sel], cov.iloc[sel]; S = S.iloc[sel] if S is not None else None
            meta['n_modelo'] = len(d); meta['n_por_EC'] = {int(e): int((d.EC == e).sum()) for e in range(1, 5)}
        cov = cov.copy()
        for j, c2 in enumerate(canceres[1:]): cov[f'CA_{c2}'] = float(c == c2)
        for c2 in canceres[1:]:
            for e in (2, 3, 4): cov[f'EC_{e}_x_{c2}'] = (ev.EC.to_numpy() == e).astype(float) * float(c == c2)
        ev = ev.copy(); ev['ca'] = k; d = d.copy(); d['CANCER'] = c
        if S is None: S = pd.DataFrame(np.nan, index=d.index, columns=range(121))
        partes.append((d, ev, cov, S, meta))
    cat = lambda i: pd.concat([p[i] for p in partes], ignore_index=True)
    d, ev, S = cat(0), cat(1), cat(3)
    cov = pd.concat([p[2] for p in partes], ignore_index=True).fillna(0.0)
    inst = d.INSTITU.astype(str) if hosp_global == 'compartilhado' else d.CANCER + '|' + d.INSTITU.astype(str)
    hosp = inst.astype('category').cat.codes.values; reg = d.DRS.astype(str).astype('category').cat.codes.values
    porc = {p[4]['cancer']: p[4] for p in partes}
    meta = dict(cancer='global', canceres=list(canceres), hosp_global=hosp_global, frac=frac, por_cancer=porc,
                D={c: m['D'] for c, m in porc.items()}, n_modelo=len(d), ml_disponivel=any(m['ml_disponivel'] for m in porc.values()),
                n_hospitais=int(hosp.max()) + 1,
                hospitais_em_2_ou_mais_canceres=int((d.groupby(d.INSTITU.astype(str)).CANCER.nunique() >= 2).sum()))
    log(f'[dados] global: {len(d)} pacientes de {len(canceres)} canceres, {meta["n_hospitais"]} codigos de hospital ({hosp_global}), '
        f'{meta["hospitais_em_2_ou_mais_canceres"]} hospitais com 2+ canceres, {cov.shape[1]} covariaveis')
    return d, ev, cov, hosp, reg, S, meta
