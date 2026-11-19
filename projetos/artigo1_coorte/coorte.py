"""
coorte.py - modelo dinamico de coorte para o RHC/SP (FOSP).
Duas versoes da censura (Secao 2.6 do artigo):
  'entrada' (versao A): censurados do mes lidos da planilha e impostos ao modelo;
  'ar'      (versao B): censurados estimados pelo modelo, c_i(t) = kappa_i [n_i(t-1) + R_i(t-1)],
                        com residuo AR(1) de coeficiente phi_i usado na previsao.
Implementa, na ordem do artigo: leitura dos dados (2.1), modelo de coorte (2.4), censura (2.6),
deconvolucao da sobrevida (2.7), estimacao (2.8), bootstrap em blocos (2.11),
estudo de simulacao (2.12) e validacao temporal (2.13).
Dependencias: numpy, scipy, pandas, openpyxl.
"""
import os, json, time
import numpy as np, pandas as pd
from scipy.optimize import least_squares, minimize

# ---------------------------------------------------------------- 2.1 Dados
CANCERES = {'colo': 'Colorretal', 'colo_utero': 'Colo do útero', 'mama': 'Mama',
            'prost': 'Próstata', 'pulm': 'Pulmão'}
N = 281          # meses usados (jan/2000 em diante, assumido)
KEST = 220       # meses de estimacao; 221 a 281 ficam para validacao
H = 60           # meses de sobrevida usados como regularizador
W = 100.0        # peso da sobrevida
L = 12           # tamanho do bloco do bootstrap
NM = ['p1','p2','p3','mu1','mu2','mu3','mu4','r1','r2','r3','r4','muQ','muR']
NM_AR = NM + ['k1','k2','k3','k4']   # versao B: taxa mensal de censura por coorte
KMAX = 0.05                           # limite superior de kappa (5% ao mes)
LB, UB = np.zeros(13), np.full(13, 0.3)
def limites(censura):
    """Limites dos parametros: 13 taxas em [0; 0,3] e, na versao B, 4 kappas em [0; 0,05]."""
    if censura == 'ar': return np.zeros(17), np.r_[np.full(13, 0.3), np.full(4, KMAX)]
    return LB, UB
def nomes(censura): return NM_AR if censura == 'ar' else NM

class Dados:
    """Series de um cancer: U[i] entradas, Y[i+1][s] saidas (A, R, O), CD/CR censurados."""
    def __init__(self, cancer, pasta, censura='entrada', remissao=None):
        assert censura in ('entrada', 'ar')
        remissao = remissao or os.environ.get('REMISSAO', 'Q')
        assert remissao in ('Q', 'S')
        self.cancer = cancer; self.censura = censura
        self.remissao = remissao   # Q: em D, so Q passa a R (original); S: em D, toda a massa viva passa a R (regra do registro)
        self.phi = np.zeros(4)                                   # versao B: coeficiente AR(1) por coorte
        self.D = 126 if cancer in ('mama', 'prost') else 66     # prazo do registro para a remissao
        self.U = np.zeros((4, N)); self.Y = {}; self.C = np.zeros((4, N))
        for i in range(1, 5):
            d = pd.read_excel(os.path.join(pasta, f'{cancer}_ec{i}.xlsx')).iloc[:N]
            self.U[i-1] = d.entradas.values
            self.Y[i] = dict(A=(d.acumulados - d.remissao).values.astype(float),
                             R=d.remissao.values.astype(float), O=d.obitos.values.astype(float))
            self.C[i-1] = d.censurados.values.astype(float)
        # CD/CR: reparticao pela fracao OBSERVADA, usada so como referencia (valkappa); simula reparte pela fracao do modelo (2.6)
        self.CD = np.zeros((4, N)); self.CR = np.zeros((4, N))
        for i in range(1, 5):
            A, R = self.Y[i]['A'], self.Y[i]['R']
            tot = np.r_[1.0, (A + R)[:-1]]; sh = np.r_[0.0, R[:-1]] / np.maximum(tot, 1)
            self.CR[i-1] = self.C[i-1] * sh; self.CD[i-1] = self.C[i-1] - self.CR[i-1]
        self.Cobs = self.C.copy()
        self.Yobs = {i: {s: v.copy() for s, v in self.Y[i].items()} for i in range(1, 5)}
        self.SK = [np.ones(H) for _ in range(4)]   # sobrevida recuperada (preenchida por recupera_sobrevida)

def escala(y):
    """sigma_{i,s}: raiz da media da serie na janela de estimacao (normalizacao tipo Poisson)."""
    return np.sqrt(max(y[:KEST].mean(), 1.0))

# ---------------------------------------------------------------- 2.4 Modelo de coorte
def par(th):
    q = dict(zip(NM, th))
    p = np.array([q['p1'], q['p2'], q['p3'], 0.]); mu = np.array([q['mu1'], q['mu2'], q['mu3'], q['mu4']])
    r = np.array([q['r1'], q['r2'], q['r3'], q['r4']])
    return p, mu, r, q['muQ'], q['muR']

def impulso(th, i, T):
    """Resposta impulsiva da coorte i (0..3) sem censura: S(tau) = 1'z + Q e o proprio Q(tau)."""
    p, mu, r, mq, _ = par(th); z = np.zeros(4); z[i] = 1; Q = 0.
    S = np.zeros(T); Qs = np.zeros(T)
    for t in range(T):
        S[t] = z.sum() + Q; Qs[t] = Q
        pr = p * z; Q = Q * (1 - mq) + r @ z
        zn = z * (1 - mu - p - r); zn[1:] += pr[:-1]; z = zn
    return S, Qs

def simula(th, dd, ate=None):
    """Simula as 4 coortes. Obitos do mes t usam o estado do inicio do mes; estoques A e R sao do fim do mes.
    Versao A: censurados c_i(t) da planilha. Versao B: c_i(t) = kappa_i (n + R) do modelo no mes anterior;
    com ate=b, usa os censurados observados ate b-1 e preve a partir de b com a correcao AR(1) phi^h e(b-1)."""
    p, mu, r, mq, mR = par(th); out = {}; ar = dd.censura == 'ar'
    for i in range(4):
        Si, Qi = impulso(th, i, dd.D + 1)
        regS = getattr(dd, 'remissao', 'Q') == 'S'
        g = Si[dd.D] if regS else Qi[dd.D]             # g_i = Q_i(D) (original) ou S_i(D) (vivos e acompanhados em D)
        z = np.zeros(4); Q = 0.; R = 0.; kap = th[13 + i] if ar else 0.; e_ult = 0.
        A = np.zeros(N); Rs = np.zeros(N); O = np.zeros(N); Cs = np.zeros(N)
        for k in range(N):
            obitos = mu @ z + mq * Q + mR * R
            pr = p * z
            Qn = Q * (1 - mq) + r @ z                    # nao morreram em Q + chegam a Q
            zn = z * (1 - mu - p - r); zn[1:] += pr[:-1] # continuam em EC j + chegam de EC j-1
            Rn = R * (1 - mR)                            # nao morreram em R
            zn[i] += dd.U[i, k]                          # novos diagnosticos (so em j = i)
            n = z.sum() + Q                              # total em tratamento (modelo)
            tot = n + R                                  # total vivo no modelo no inicio do mes
            if not ar: c = dd.C[i, k]                    # versao A: censurados da planilha
            elif ate is not None and k < ate:            # versao B, passado conhecido: dado observado
                c = dd.C[i, k]; e_ult = c - kap * tot
            else:                                        # versao B: censura estimada (+ AR(1) na previsao)
                c = kap * tot + (dd.phi[i] ** (k - ate + 1) * e_ult if ate is not None else 0.)
                c = min(max(c, 0.), tot)
            Cs[k] = c
            cR = c * R / tot if tot > 0 else 0.          # 2.6: reparticao pela fracao em remissao do MODELO
            cD = c - cR                                  #      (garante cR <= R e R >= 0)
            if n > 0: zn -= cD * z / n; Qn -= cD * Q / n # censurados em tratamento, proporcionais
            else: zn[i] -= cD                            # caso de borda: coorte ainda vazia
            Rn -= cR                                     # censurados em remissao
            if k >= dd.D:                                # regra do registro: D meses
                tr = g * dd.U[i, k - dd.D]
                if not regS: Qn -= tr                    # original: a coorte de k-D sai de Q
                else:                                    # variante S: sai de z e Q, proporcionalmente
                    nn = zn.sum() + Qn
                    tr = min(tr, max(nn, 0.))
                    if nn > 0: zn = zn - tr * zn / nn; Qn -= tr * Qn / nn
                Rn += tr
            z, Q, R = zn, Qn, Rn
            A[k] = z.sum() + Q; Rs[k] = R; O[k] = obitos
        out[i+1] = dict(A=A, R=Rs, O=O, C=Cs, g=g)
    return out

# ---------------------------------------------------------------- 2.7 Sobrevida por deconvolucao
EDGES = np.array([0, 3, 6, 12, 18, 24, 36, 48, 60, 84, 120, 180, 400])
def risco(v):
    tau = np.arange(400); idx = np.searchsorted(EDGES, tau, side='right') - 1
    return 1 / (1 + np.exp(-v[idx]))

def obitos_esperados(h, E, C, K):
    """Propaga as entradas por tempo desde a entrada (v_t(tau)), retira censurados, devolve os obitos esperados."""
    T = K + 1; v = np.zeros(T); Do = np.zeros(K)
    for k in range(K):
        v = np.roll(v, 1); v[0] = E[k]
        d = v * h[:T]; Do[k] = d.sum(); s = v - d
        base = s.sum(); g = min(C[k] / base, 1) if base > 0 else 0
        v = s * (1 - g)
    return Do

def deconvolucao(E, O, C, a=0, b=280, lam=10.0):
    """Maxima verossimilhanca de Poisson penalizada nos meses [a, b). Devolve risco h e sobrevida S."""
    def nll(v):
        Dd = obitos_esperados(risco(v), E, C, b) + 1e-9
        return np.sum((Dd - O[:b] * np.log(Dd))[a:b]) + lam * np.sum(np.diff(v) ** 2)
    rr = minimize(nll, np.full(len(EDGES) - 1, -4.0), method='L-BFGS-B', options={'maxiter': 3000})
    h = risco(rr.x); return h, np.concatenate([[1], np.cumprod(1 - h)])

def recupera_sobrevida(dd, a=0, b=280):
    """Preenche dd.SK com a sobrevida recuperada de cada coorte; devolve as curvas completas."""
    Ss = []
    for i in range(1, 5):
        _, S = deconvolucao(dd.U[i-1], dd.Y[i]['O'], dd.C[i-1], a, b)
        dd.SK[i-1] = S[:H].copy(); Ss.append(S)
    return Ss

# ---------------------------------------------------------------- 2.8 Estimacao
def residuos(th, dd, a=0, b=KEST):
    m = simula(th, dd)
    rr = [(m[i][s][a:b] - dd.Y[i][s][a:b]) / escala(dd.Y[i][s]) for i in range(1, 5) for s in 'ARO']
    if dd.censura == 'ar':                                # versao B: censurados tambem sao saida
        rr += [(m[i]['C'][a:b] - dd.C[i-1][a:b]) / escala(dd.C[i-1]) for i in range(1, 5)]
    rr += [W * (impulso(th, i, H)[0] - dd.SK[i]) for i in range(4)]
    return np.concatenate(rr)

def estima(dd, partidas=6, inicio=None, a=0, b=KEST, max_nfev=400, seed=0):
    """Minimos quadrados com limites 0..0,3 (trust region reflective). Devolve theta e custo."""
    best = None; rng = np.random.default_rng(seed); lb, ub = limites(dd.censura)
    for s in range(partidas):
        x0 = inicio if (inicio is not None and s == 0) else rng.uniform(0.001, 0.05, 13)
        if dd.censura == 'ar' and len(x0) == 13: x0 = np.r_[x0, rng.uniform(0.0005, 0.01, 4)]
        r = least_squares(lambda x: residuos(x, dd, a, b), np.clip(x0, lb + 1e-6, ub - 1e-3),
                          bounds=(lb, ub), x_scale='jac', max_nfev=max_nfev)
        if best is None or r.cost < best.cost: best = r
    if dd.censura == 'ar': estima_phi(best.x, dd, a, b)
    return best.x, best.cost

def estima_phi(th, dd, a=0, b=KEST):
    """Versao B: coeficiente AR(1) do residuo da censura, e_i(t) = c_i(t) - c_hat_i(t), na janela [a, b)."""
    m = simula(th, dd)
    for i in range(4):
        e = dd.C[i, a:b] - m[i+1]['C'][a:b]
        dd.phi[i] = float(np.clip(np.sum(e[1:] * e[:-1]) / max(np.sum(e[:-1] ** 2), 1e-9), 0, 0.99))
    return dd.phi.copy()

def ajuste(y, yh, a, b):
    """Qualidade do ajuste em % (1 - erro relativo)."""
    return 100 * (1 - np.linalg.norm(y[a:b] - yh[a:b]) / np.linalg.norm(y[a:b] - y[a:b].mean()))

# ---------------------------------------------------------------- 2.10 Identificabilidade (perfis)
def estima_fixo(dd, fixos, inicio, partidas=2, max_nfev=400, seed=0):
    """Estima com alguns parametros fixados (dict nome->valor)."""
    NMv = nomes(dd.censura); LBv, UBv = limites(dd.censura)
    livre = np.array([n not in fixos for n in NMv])
    def cheio(x):
        t = inicio.copy(); t[livre] = x
        for k, v in fixos.items(): t[NMv.index(k)] = v
        return t
    best = None; rng = np.random.default_rng(seed)
    for s in range(partidas):
        x0 = inicio[livre] if s == 0 else np.r_[rng.uniform(0.001, 0.05, 13), rng.uniform(0.0005, 0.01, len(NMv) - 13)][livre]
        r = least_squares(lambda x: residuos(cheio(x), dd), np.clip(x0, LBv[livre] + 1e-6, UBv[livre] - 1e-3),
                          bounds=(LBv[livre], UBv[livre]), x_scale='jac', max_nfev=max_nfev)
        if best is None or r.cost < best.cost: best = r
    return cheio(best.x), best.cost

def perfil(dd, th0, nome, grade=(0, .002, .005, .01, .02, .04, .08, .15)):
    """Fixa uma taxa de progressao em cada valor da grade e reestima as demais.
    Devolve (valor, fracao da coorte que progride, aumento do custo, erro maximo na sobrevida em pontos %)."""
    j = int(nome[1]) - 1; out = []
    for v in grade:
        t, c = estima_fixo(dd, {nome: v}, th0)
        p, mu, r, _, _ = par(t); f = p[j] / (mu[j] + p[j] + r[j] + 1e-12)
        eS = max(np.abs(impulso(t, i, H)[0] - dd.SK[i]).max() for i in range(4))
        out.append((v, f, c, 100 * eS))
    return out

# ---------------------------------------------------------------- 2.11 Bootstrap em blocos
def residuos_bootstrap(dd, m):
    """Obitos: observado - ajustado. Estoques: diferenca das variacoes mensais."""
    RES = {}
    for i in range(1, 5):
        RES[(i, 'O')] = dd.Yobs[i]['O'] - m[i]['O']
        for s in 'AR': RES[(i, s)] = np.diff(np.r_[0, dd.Yobs[i][s]]) - np.diff(np.r_[0, m[i][s]])
        if dd.censura == 'ar': RES[(i, 'C')] = dd.Cobs[i-1] - m[i]['C']   # versao B: residuo da censura
    return RES

def blocos(rng):
    """Blocos de 12 meses iniciados sempre no mesmo mes do calendario; mesmo sorteio para todas as series."""
    st = L * rng.integers(0, (N - L) // L + 1, N // L + 1)
    return np.concatenate([np.arange(a, a + L) for a in st])[:N]

def serie_sintetica(m, RES, idx):
    Y = {}
    for i in range(1, 5):
        Y[i] = {'O': np.maximum(m[i]['O'] + RES[(i, 'O')][idx], 0)}
        for s in 'AR': Y[i][s] = np.maximum(m[i][s] + np.cumsum(RES[(i, s)][idx]), 0)
        if (i, 'C') in RES: Y[i]['C'] = np.maximum(m[i]['C'] + RES[(i, 'C')][idx], 0)
    return Y

def usa_series(dd, Y):
    """Coloca as series Y (sinteticas) no lugar dos dados; na versao B inclui os censurados."""
    for i in range(1, 5):
        for s in 'ARO': dd.Y[i][s] = Y[i][s].copy()
        if 'C' in Y[i]: dd.C[i-1] = Y[i]['C'].copy()

def restaura(dd):
    for i in range(1, 5):
        for s in 'ARO': dd.Y[i][s] = dd.Yobs[i][s].copy()
    dd.C = dd.Cobs.copy()

def reestima(dd, Y, partidas=1, inicio=None, seed=0):
    """Refaz deconvolucao e estimacao numa serie sintetica Y (entradas e censuras fixas)."""
    usa_series(dd, Y)
    Ss = recupera_sobrevida(dd)
    th, _ = estima(dd, partidas=partidas, inicio=inicio, seed=seed)
    restaura(dd)
    return th, Ss

def resumo(th, dd):
    return {'S': [[float(v) for v in impulso(th, i, 121)[0][[12, 60, 120]]] for i in range(4)],
            'g': [float(impulso(th, i, dd.D + 1)[1][dd.D]) for i in range(4)]}

def bootstrap(dd, th0, B=200, semente=1000, arquivo=None, inicio_rep=0):
    """B replicas; cada uma parte da estimativa pontual th0 (1 partida). Grava uma linha JSON por replica."""
    m0 = simula(th0, dd); RES = residuos_bootstrap(dd, m0)
    rng = np.random.default_rng(semente + inicio_rep); out = []
    for b in range(inicio_rep, inicio_rep + B):
        t = time.time(); idx = blocos(rng)
        th, Ss = reestima(dd, serie_sintetica(m0, RES, idx), partidas=1, inicio=th0)
        rec = dict(b=b, theta=th.tolist(), S=[list(map(float, s[[0, 12, 24, 36, 60, 120]])) for s in Ss],
                   g=resumo(th, dd)['g'], sec=time.time() - t)
        out.append(rec)
        if arquivo:
            with open(arquivo, 'a') as f: f.write(json.dumps(rec) + '\n')
    return out

# ---------------------------------------------------------------- 2.12 Estudo de simulacao
def cenarios(th0):
    sc = [('realista', th0.copy())]
    for v in (0.0, 0.005, 0.01, 0.02):
        t = th0.copy(); t[:3] = v; sc.append((f'p={v}', t))
    return sc

def simulacao_vies(dd, th0, n_series=50, arquivo=None, cenario=None, inicio=0):
    """Para cada cenario, gera series com theta conhecido e reestima com 3 partidas aleatorias."""
    m0 = simula(th0, dd); RES = residuos_bootstrap(dd, m0); out = []
    for k, (nome, tt) in enumerate(cenarios(th0)):
        if cenario is not None and nome != cenario: continue
        mt = simula(tt, dd); verdade = resumo(tt, dd)
        for r in range(inicio, inicio + n_series):   # inicio: permite dividir as series entre tarefas
            t = time.time(); rng = np.random.default_rng(10000 * k + r)
            th, Ss = reestima(dd, serie_sintetica(mt, RES, blocos(rng)), partidas=3)
            rec = dict(cen=nome, r=r, true=tt.tolist(), est=th.tolist(), true_s=verdade, est_s=resumo(th, dd),
                       dec60=[float(s[60]) for s in Ss], sec=time.time() - t)
            out.append(rec)
            if arquivo:
                with open(arquivo, 'a') as f: f.write(json.dumps(rec) + '\n')
    return out

def simulacao_cobertura(dd, th0, series=range(30), B=50, arquivo=None):
    """Cenario realista: em cada serie simulada, estima e aplica o mesmo bootstrap (B replicas)."""
    m0 = simula(th0, dd); RES = residuos_bootstrap(dd, m0); verdade = resumo(th0, dd); out = []
    Yobs0 = {i: {s: v.copy() for s, v in dd.Yobs[i].items()} for i in range(1, 5)}; C0 = dd.Cobs.copy()
    for r in series:
        t = time.time(); rng = np.random.default_rng(50000 + r)
        Y = serie_sintetica(m0, RES, blocos(rng))
        th, Ss = reestima(dd, Y, partidas=3)
        # bootstrap dentro da serie sintetica
        for i in range(1, 5):
            for s in 'ARO': dd.Yobs[i][s], dd.Y[i][s] = Y[i][s].copy(), Y[i][s].copy()
            if 'C' in Y[i]: dd.Cobs[i-1] = Y[i]['C'].copy(); dd.C[i-1] = Y[i]['C'].copy()
        mh = simula(th, dd); resb = residuos_bootstrap(dd, mh); Bs = []
        for b in range(B):
            thb, Sb = reestima(dd, serie_sintetica(mh, resb, blocos(rng)), partidas=1, inicio=th)
            Bs.append(dict(est=thb.tolist(), est_s=resumo(thb, dd), dec60=[float(s[60]) for s in Sb]))
        for i in range(1, 5):
            for s in 'ARO': dd.Yobs[i][s], dd.Y[i][s] = Yobs0[i][s].copy(), Yobs0[i][s].copy()
        dd.Cobs = C0.copy(); dd.C = C0.copy()
        rec = dict(r=r, true=th0.tolist(), true_s=verdade, est=th.tolist(), est_s=resumo(th, dd),
                   dec60=[float(s[60]) for s in Ss], boot=Bs, sec=time.time() - t)
        out.append(rec)
        if arquivo:
            with open(arquivo, 'a') as f: f.write(json.dumps(rec) + '\n')
    return out

# ---------------------------------------------------------------- 2.13 Validacao temporal
def wape(y, yh): return float(np.sum(np.abs(y - yh)) / max(np.sum(y), 1))

def validacao(dd, janelas=(24, 36, 60, 96, 120), horizontes=(12, 36, 60), passo=24, arquivo=None):
    """Ajusta em [b-W, b) e preve [b, b+h). Sobrevida recuperada so com a janela; 3 partidas aleatorias."""
    out = []
    for Wj in janelas:
        for b in range(Wj, N - 12 + 1, passo):
            t = time.time(); a = b - Wj
            hs = []
            for i in range(1, 5):
                h, S = deconvolucao(dd.U[i-1], dd.Yobs[i]['O'], dd.C[i-1], a, b); hs.append(h); dd.SK[i-1] = S[:H].copy()
            th, _ = estima(dd, partidas=3, inicio=None, a=a, b=b, max_nfev=1500)
            m = simula(th, dd, ate=b if dd.censura == 'ar' else None)   # B: censura prevista a partir de b
            rec = dict(W=Wj, b=b, censura=dd.censura, theta=th.tolist(), phi=dd.phi.tolist(), err={}, base={})
            for hz in horizontes:
                if b + hz > N: continue
                e, bs = {}, {}
                for i in range(1, 5):
                    for s in 'ARO': e[f'{s}{i}'] = wape(dd.Yobs[i][s][b:b+hz], m[i][s][b:b+hz])
                    if dd.censura == 'ar': e[f'C{i}'] = wape(dd.Cobs[i-1][b:b+hz], m[i]['C'][b:b+hz])
                O = sum(dd.Yobs[i]['O'][b:b+hz] for i in range(1, 5))
                e['Otot'] = wape(O, sum(m[i]['O'][b:b+hz] for i in range(1, 5)))
                bs['pers_tot'] = wape(O, sum(np.array([dd.Yobs[i]['O'][b-12+(k % 12)] for k in range(hz)]) for i in range(1, 5)))
                bs['dec_tot'] = wape(O, sum(obitos_esperados(hs[i-1], dd.U[i-1], dd.C[i-1], b+hz)[b:b+hz] for i in range(1, 5)))
                rec['err'][hz] = e; rec['base'][hz] = bs
            rec['sec'] = time.time() - t; out.append(rec)
            if arquivo:
                with open(arquivo, 'a') as f: f.write(json.dumps(rec) + '\n')
    return out
