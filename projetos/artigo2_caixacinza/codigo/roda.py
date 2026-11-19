"""Artigo 2: uma rodada completa do modelo caixa-cinza (RedeM2) para um cancer.

Etapa A: maxima verossimilhanca por paciente (W = 0), parada antecipada na validacao.
Etapa B: custo hibrido J = sum_n -log L_n + W sum_{s,i,t} [(yhat - y)/sigma]^2, partindo de A,
         com s em {obitos O, vivos acompanhados V, remissao administrativa Rad}.
Depois: avaliacao no conjunto de teste e cenarios contrafactuais em toda a populacao.

Exemplo: python roda.py --cancer pulmao --raiz ../dados --W 0.1 --saida ../resultados/pulmao_base
"""
import argparse, json, os, time, pickle, sys
p = argparse.ArgumentParser()
p.add_argument('--cancer', required=True, help="um cancer, ou 'global' (os de --canceres num modelo so, o cancer como seletor)")
p.add_argument('--canceres', default='colorretal,colo_utero,pulmao,mama,prostata', help='global: lista; o primeiro e a referencia das taxas de base')
p.add_argument('--hosp_global', default='compartilhado', choices=['compartilhado', 'por_cancer'], help='global: um efeito por hospital, ou um por (cancer, hospital)')
p.add_argument('--frac', type=float, default=1.0, help='global: fracao de pacientes de cada cancer (teste rapido)')
p.add_argument('--vigil', type=int, default=None, help='1: estado de vigilancia V (o mesmo que VIGIL=1)')
p.add_argument('--fase', type=int, default=None, help='1: fase inicial do tratamento T (o mesmo que FASE=1)')
p.add_argument('--raiz', default=os.path.join(os.path.dirname(__file__), '..', 'dados'))
p.add_argument('--ini', default=os.path.join(os.path.dirname(__file__), '..', 'ini'))
p.add_argument('--saida', required=True)
p.add_argument('--W', type=float, default=0.1)
p.add_argument('--L', type=float, default=1.2)
p.add_argument('--semente', type=int, default=2026)
p.add_argument('--boot', type=int, default=-1, help='>=0: reamostra os pacientes de treino com reposicao')
p.add_argument('--divisao', default='aleatoria', choices=['aleatoria', 'temporal'])
p.add_argument('--corte', type=int, default=2015, help='divisao temporal: teste = origem >= corte')
p.add_argument('--ablacao', default='completo', choices=['completo', 'sem_hosp', 'sem_reg', 'so_EC'])
p.add_argument('--nivel', type=int, default=3, help='1: so sobrevida; 2: + tratamento/recidiva; 3: + ULTINFO')
p.add_argument('--origem', default='consulta', choices=['consulta', 'diagnostico'])
p.add_argument('--D', type=int, default=None, help='forca D (senao detecta pela serie de remissao)')
p.add_argument('--epA', type=int, default=80)
p.add_argument('--epB', type=int, default=40)
p.add_argument('--antecipa', default='0.2', help='fracoes de EC2-4 antecipadas um estadio nos cenarios, ex.: 0.1,0.2,0.5')
p.add_argument('--cenarios', type=int, default=1)
p.add_argument('--verifica', type=int, default=1, help='calibracao por hospital, IPW e troca de hospital dentro do tipo')
p.add_argument('--carrega_rede', default='', help='pula o treino e usa estes pesos (mesma semente => mesma divisao)')
p.add_argument('--exclui_reg', type=int, default=-1, help='>=0: deixa de fora a regiao (codigo DRS 0..) e testa nela')
p.add_argument('--placebo', type=int, default=0, help='>0: embaralha hospital e tipo de hospital entre pacientes (controle negativo)')
p.add_argument('--figuras', type=int, default=0)
p.add_argument('--espera', default='comum', choices=['comum', 'ec'], help='ec: taxas de base de E (gamma, mu_E) por EC de entrada')
p.add_argument('--LE', type=float, default=None, help='limite do fator da rede nas taxas de E (padrao = L)')
a = p.parse_args()
os.makedirs(a.saida, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if a.vigil is not None: os.environ['VIGIL'] = str(a.vigil)      # precisa vir antes de importar core
if a.fase is not None: os.environ['FASE'] = str(a.fase)
from modelo import *
from rede import RedeM2, taxas_iniciais
import dados
LOG = open(os.path.join(a.saida, 'log.txt'), 'a')
def log(*x):
    s = ' '.join(str(v) for v in x); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()
log('[args]', json.dumps(vars(a)))
torch.manual_seed(a.semente); T0 = time.time()

# ---------------- dados
GLOBAL = a.cancer == 'global'
if GLOBAL:
    CAN = a.canceres.split(',')
    d, ev, cov, hosp, reg, Sml, meta = dados.carrega_global(CAN, a.raiz, a.origem, a.D, log, a.hosp_global, a.frac, a.semente)
else:
    CAN = [a.cancer]
    d, ev, cov, hosp, reg, Sml, meta = dados.carrega(a.cancer, a.raiz, a.origem, a.D, log); ev['ca'] = 0
log(f"[estados] {NOMES_ESTADOS}; taxas {NOMES_TAXAS}")
Dm = meta['D']; TA = dados.T_FIM_OBS
D_de = lambda k: meta['D'][CAN[k]] if GLOBAL else Dm
CAv = ev.ca.to_numpy()
if a.ablacao == 'so_EC': cov = cov[[c for c in cov.columns if c.startswith(('EC_', 'CA_'))]]
if a.ablacao in ('sem_hosp', 'so_EC'): hosp = np.zeros_like(hosp)
if a.ablacao in ('sem_reg', 'so_EC'): reg = np.zeros_like(reg)
if a.placebo > 0:                                     # controle negativo: hospital sem relacao com o desfecho
    rp = np.random.default_rng(500 + a.placebo); pm = np.arange(len(d))
    for k in range(len(CAN)): ix = np.where(CAv == k)[0]; pm[ix] = rp.permutation(ix)     # dentro de cada cancer
    hcols = [c for c in cov.columns if c.startswith('HABILIT_HOSP_')]
    cov[hcols] = cov[hcols].to_numpy()[pm]; hosp = hosp[pm]; d['HABILIT_HOSP'] = d.HABILIT_HOSP.to_numpy()[pm]
    log('[placebo] hospital e tipo de hospital embaralhados entre pacientes')
cols = list(cov.columns)
Z = torch.as_tensor(cov.to_numpy(float)); h = torch.as_tensor(hosp.copy()).long(); rg = torch.as_tensor(reg.copy()).long()
ec = torch.as_tensor(ev.EC.to_numpy().copy()).long(); Dc = torch.as_tensor(ev.Dc.to_numpy().copy()).long()
td = torch.as_tensor(ev.t_diag.to_numpy().copy()).long()
cens = torch.as_tensor(censura_potencial(ev)).long()
DD = tensores(ev, a.nivel); N = len(ev)
ECv = ev.EC.to_numpy(); tau = ev.tau.to_numpy(); dob = ev.d_obito.to_numpy()

# ---------------- divisao treino / validacao / teste
def divide(ix):
    """Divisao dentro de um cancer (ix = indices globais). Com ix = 0..N-1 e a mesma semente, e a divisao do
    modelo separado: o modelo global testa exatamente nos mesmos pacientes que os modelos por cancer."""
    rng = np.random.default_rng(a.semente)
    if a.exclui_reg >= 0:                              # validacao espacial: uma regiao fica de fora
        fora = ix[reg[ix] == a.exclui_reg]; dentro = ix[reg[ix] != a.exclui_reg]
        perm = rng.permutation(dentro); itr = perm[:int(.85 * len(perm))]; iva = perm[int(.85 * len(perm)):]; ite = fora; P = dentro
    elif a.divisao == 'aleatoria':
        n = len(ix); perm = rng.permutation(ix); itr = perm[:int(.7 * n)]; iva = perm[int(.7 * n):int(.85 * n)]; ite = perm[int(.85 * n):]
        P = ix                                         # pacientes cujas series entram no custo hibrido
    else:
        ano = 2000 + ev.t_diag.to_numpy()[ix] // 12
        antes = ix[ano < a.corte]; ite = ix[ano >= a.corte]
        perm = rng.permutation(antes); itr = perm[:int(.85 * len(perm))]; iva = perm[int(.85 * len(perm)):]; P = antes
    if a.boot >= 0:
        itr = np.random.default_rng(10_000 + a.boot).choice(itr, len(itr), replace=True)
    return itr, iva, ite, P
if a.exclui_reg >= 0 and (reg == a.exclui_reg).sum() < 50:
    log(f'[fim] regiao {a.exclui_reg} com {(reg == a.exclui_reg).sum()} pacientes: nada a testar'); sys.exit(0)
partes = [divide(np.where(CAv == k)[0]) for k in range(len(CAN))]
itr, iva, ite, P = [np.concatenate([p[j] for p in partes]) for j in range(4)]
log(f'[divisao] {a.divisao}: treino {len(itr)}, validacao {len(iva)}, teste {len(ite)}; series sobre {len(P)} pacientes')
itr, iva, ite, Pt = map(lambda x: torch.as_tensor(np.asarray(x)).long(), (itr, iva, ite, P))

# ---------------- series observadas por EC (a partir da tabela)
# grupos = (cancer, EC): 4 por cancer; no modelo de um cancer, grupo = EC - 1
NG = 4 * len(CAN); grp = torch.as_tensor(CAv * 4 + ECv - 1).long()
Y = np.zeros((3, NG, TA))
for k in range(len(CAN)):
    for e in range(1, 5):
        Y[:, 4 * k + e - 1] = dados.series_observadas(ev.iloc[P][(ECv[P] == e) & (CAv[P] == k)], D_de(k), TA)
S2 = torch.as_tensor(np.maximum(Y.mean(2, keepdims=True), 1.0)); Yt = torch.as_tensor(Y)

def saidas_cal(th, idx, ecx=None):
    """(O, V, Rad, Rlat, A) por paciente em tempo de calendario."""
    ecx = ec[idx] if ecx is None else ecx
    H = int((torch.minimum(cens[idx], torch.tensor(TA - 1)) - td[idx]).max().clamp(min=1))
    xi = simula_xi(th, ecx, Dc[idx], H); S, O, Rl, A = saidas_paciente(th, xi)
    tt = torch.arange(H + 1).unsqueeze(0); tc = td[idx].unsqueeze(1) + tt
    ok = (tc <= cens[idx].unsqueeze(1)) & (tc < TA)
    Rad = S * (tt >= Dc[idx].unsqueeze(1))
    return torch.stack([O, S, Rad, Rl, A], 0), tc.clamp(max=TA - 1), ok

def series_modelo(rede, idx, Zx=None, emb=None, ecx=None, mult=None, lote=6000):
    """Superposicao por grupo (EC original do paciente): (5 saidas, NG, TA)."""
    yh = torch.zeros(5, NG, TA)
    with torch.no_grad():
        for i in range(0, len(idx), lote):
            b = idx[i:i + lote]
            th = rede((Z if Zx is None else Zx)[b], h[b], rg[b], hosp_emb=None if emb is None else emb[b], mult=mult)
            out, tc, ok = saidas_cal(th, b, None if ecx is None else ecx[b])
            fl = (grp[b].unsqueeze(1) * TA + tc)[ok]
            for s in range(5): yh[s].view(-1).index_add_(0, fl, out[s][ok])
    return yh

sub = lambda Dd, i: {k: (v[i] if torch.is_tensor(v) else v) for k, v in Dd.items()}
def nll_val(rede):
    with torch.no_grad(): return -log_vero(rede(Z[iva], h[iva], rg[iva]), ec[iva], sub(DD, iva)).mean().item()

# ---------------- etapa A: verossimilhanca
ini_de = lambda c: taxas_iniciais(os.path.join(a.ini, f'ajuste_{dados.PREFIXO[c]}_entrada.json'))
ini0 = ini_de(CAN[0]); lg = lambda q, n: np.log(max(q[n], 1e-3))
offC = [[lg(ini_de(c), n) - lg(ini0, n) for n in NOMES_TAXAS] for c in CAN[1:]]   # taxas de base de cada cancer (Artigo 1)
rede = RedeM2(Z.shape[1], int(h.max()) + 1, int(rg.max()) + 1, ini0, L=a.L,
              ec_cols=[cols.index(c) for c in cols if c.startswith('EC_')] if a.espera == 'ec' else None, LE=a.LE,
              ca_cols=[cols.index(f'CA_{c}') for c in CAN[1:]] if GLOBAL else None, offC_ini=offC if GLOBAL else None)
opt = torch.optim.AdamW(rede.parameters(), lr=3e-3, weight_decay=0.); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epA)
melhor, sem, histA = np.inf, 0, []; arqA = os.path.join(a.saida, 'redeA.pt')
if a.carrega_rede: a.epA = 0; a.epB = 0
for ep in range(a.epA):
    rede.train(); pp = itr[torch.randperm(len(itr))]; L = 0
    for i in range(0, len(pp), 4096):
        b = pp[i:i + 4096]; th = rede(Z[b], h[b], rg[b])
        loss = -log_vero(th, ec[b], sub(DD, b)).mean() + rede.penalidade()
        opt.zero_grad(); loss.backward(); opt.step(); L += loss.item() * len(b) / len(pp)
    sch.step(); rede.eval(); Lv = nll_val(rede); histA.append((L, Lv))
    log(f'A epoca {ep} treino {L:.5f} validacao {Lv:.5f} t={time.time()-T0:.0f}s')
    if Lv < melhor - 1e-4: melhor, sem = Lv, 0; torch.save(rede.state_dict(), arqA)
    else: sem += 1
    if sem >= 10: log('A parada antecipada'); break
rede.load_state_dict(torch.load(a.carrega_rede if a.carrega_rede else arqA)); rede.eval()

# ---------------- etapa B: custo hibrido
histB = []
if a.W > 0 and a.epB > 0:
    opt = torch.optim.AdamW(rede.parameters(), lr=1e-3, weight_decay=0.); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epB)
    melhor = np.inf; arqB = os.path.join(a.saida, 'redeB.pt'); NP = len(Pt)
    for ep in range(a.epB):
        rede.eval(); yh = series_modelo(rede, Pt)[:3]
        J = (a.W * ((yh - Yt) ** 2 / S2).sum()).item(); G = 2 * a.W * (yh - Yt) / S2
        rede.train(); pp = itr[torch.randperm(len(itr))]; L = 0
        for i in range(0, len(pp), 4096):
            b = pp[i:i + 4096]; th = rede(Z[b], h[b], rg[b])
            nll = -log_vero(th, ec[b], sub(DD, b)).sum()
            out, tc, ok = saidas_cal(th, b); gb = G[:, grp[b], :]
            sur = sum((gb[s].gather(1, tc) * out[s] * ok).sum() for s in range(3))
            loss = nll / len(b) + sur * NP / (len(itr) * len(b)) + rede.penalidade()
            opt.zero_grad(); loss.backward(); opt.step(); L += nll.item() / len(itr)
        sch.step(); rede.eval(); Lv = nll_val(rede); tot = Lv * NP + J
        w = [((yh[k] - Yt[k]).abs().sum() / Yt[k].sum()).item() for k in range(3)]
        histB.append((L, Lv, J) + tuple(w))
        log(f'B epoca {ep} nll_tr {L:.4f} nll_va {Lv:.4f} J {J:.0f} WAPE O {w[0]:.3f} V {w[1]:.3f} Rad {w[2]:.3f} t={time.time()-T0:.0f}s')
        if tot < melhor: melhor = tot; torch.save(rede.state_dict(), arqB)
    rede.load_state_dict(torch.load(arqB)); rede.eval()

# ---------------- avaliacao (avalia.py), por cancer
AV = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'avalia.py'), encoding='utf-8').read()
if not GLOBAL:
    exec(AV)
else:
    saida0, N0, meta0, histA0, histB0 = a.saida, N, meta, histA, histB
    G0 = dict(Z=Z, h=h, rg=rg, ec=ec, Dc=Dc, td=td, cens=cens, DD=DD, ev=ev, d=d, Sml=Sml, ECv=ECv, tau=tau, dob=dob,
              itr=itr, iva=iva, ite=ite, CAv=CAv, hosp=hosp, reg=reg, Yg=Y)
    resumo_ca = {}
    for kc, cn in enumerate(CAN):
        ix = np.where(G0['CAv'] == kc)[0]; ixt = torch.as_tensor(ix).long()
        pos = -np.ones(N0, dtype=np.int64); pos[ix] = np.arange(len(ix))
        loc = lambda t: (lambda q: torch.as_tensor(q[q >= 0]).long())(pos[t.numpy()])
        Z, h, rg, ec, Dc, td, cens = (G0[k][ixt] for k in ('Z', 'h', 'rg', 'ec', 'Dc', 'td', 'cens'))
        DD = sub(G0['DD'], ixt); ev, d, Sml = (G0[k].iloc[ix] for k in ('ev', 'd', 'Sml'))
        ECv, tau, dob, CAv, hosp, reg = (G0[k][ix] for k in ('ECv', 'tau', 'dob', 'CAv', 'hosp', 'reg'))
        itr, iva, ite = loc(G0['itr']), loc(G0['iva']), loc(G0['ite'])
        Pt = loc(torch.as_tensor(P)); N = len(ix); NG = 4; grp = (ec - 1).long()
        Y = G0['Yg'][:, 4 * kc:4 * kc + 4]
        meta = dict(meta0['por_cancer'][cn], modelo='global', canceres=CAN, hosp_global=a.hosp_global, frac=a.frac)
        Dm = meta['D']; a.saida = os.path.join(saida0, cn); os.makedirs(a.saida, exist_ok=True)
        log(f'[global] avaliacao de {cn}: {N} pacientes, teste {len(ite)}')
        exec(AV)
        resumo_ca[cn] = dict(nll_teste=res['nll_teste'], cindex={k: v for k, v in res['cindex'].items() if k != 'porEC'},
                             S60=[(r['EC'], r['KM_teste'], r['modelo']) for r in res['S60']], ECE_S60=res['ECE_S60'],
                             wape_total={k: v['total'] for k, v in res['wape'].items()},
                             OE_fora_IC95_teste=res.get('calib_hospital', {}).get('teste', {}).get('fora_IC95'),
                             ipw_cacon=res.get('ipw_cacon'), placebo_troca=res.get('placebo_troca_hospital_mesmo_tipo'))
    a.saida = saida0
    json.dump(dict(args=vars(a), meta={k: v for k, v in meta0.items() if k != 'por_cancer'}, histA=histA0, histB=histB0,
                   por_cancer=resumo_ca, offC_final=dict(zip(CAN[1:], rede.offC.detach().numpy().round(4).tolist())),
                   tempo_s=time.time() - T0), open(os.path.join(saida0, 'resultado_global.json'), 'w'), default=float, indent=1)
    log(f'[fim global] {time.time() - T0:.0f}s')
