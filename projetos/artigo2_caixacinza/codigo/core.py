# ==== CELULA: setup
import numpy as np, pandas as pd, torch, torch.nn as nn, math, time

torch.set_default_dtype(torch.float64)
DEV = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
SEED = 2026
np.random.seed(SEED); torch.manual_seed(SEED)


# ==== CELULA: constantes
# Estados (ordem do vetor xi): E, z1, z2, z3, z4, Q, R
import os as _os
VIGIL = _os.environ.get('VIGIL', '0') == '1'      # 1: acrescenta o estado de vigilancia V (sem tratamento, anos)
FASE = _os.environ.get('FASE', '0') == '1'        # 1: fase inicial do tratamento T (memoria: risco alto no inicio)
E, Z1, Z2, Z3, Z4, Q, R = range(7)
V = 7 if VIGIL else -1
T = 7 + int(VIGIL) if FASE else -1
NS = 7 + int(VIGIL) + int(FASE)
NOMES_ESTADOS = ['E', 'z1', 'z2', 'z3', 'z4', 'Q', 'R'] + (['V'] if VIGIL else []) + (['T'] if FASE else [])
# Taxas (ordem do vetor theta, Secao 5, Bloco M1)
NOMES_TAXAS = ['gamma', 'mu_E', 'mu_1', 'mu_2', 'mu_3', 'mu_4',
               'p_1', 'p_2', 'p_3', 'r_1', 'r_2', 'r_3', 'r_4', 'rho', 'mu_Q', 'mu_R'] + \
              (['nu', 'delta', 'mu_V'] if VIGIL else []) + \
              (['kappa', 'mu_T'] if FASE else [])          # T -> z_EC (fim da fase inicial), obito em T
IX = {n: i for i, n in enumerate(NOMES_TAXAS)}
K = len(NOMES_TAXAS)  # 16
TETO = torch.full((K,), 0.3); TETO[0] = 0.9          # theta_max (gamma = 0,9) [IA-9]
SAIDA_MAX = 0.9                                       # soma maxima das saidas de cada estado
# Grupos de saidas por estado de origem: E, z1..z4, Q, R (p_4 = 0)
GRUPOS = [[0, 1], [2, 6, 9], [3, 7, 10], [4, 8, 11], [5, 12], [13, 14], [15]]
if VIGIL: GRUPOS[0] = [0, 1, IX['nu']]; GRUPOS.append([IX['delta'], IX['mu_V']])
if FASE: GRUPOS.append([IX['kappa'], IX['mu_T']])
G_MAT = torch.zeros(K, len(GRUPOS))
for g, idx in enumerate(GRUPOS):
    G_MAT[idx, g] = 1.0
D_C = {'mama': 126, 'prostata': 126, 'pulmao': 66, 'colorretal': 66, 'colo_utero': 66}
T_TOTAL = 303   # meses de jan/2000 a abr/2025 (extracao nova)
torch.set_num_threads(int(__import__("os").environ.get("NTHREADS", "4")))
K_TREINO = 220  # validacao temporal: treino nos meses 1..220

# ==== CELULA: M1 limites
def limita_taxas(eta, eps=1e-8):
    """eta (N,16) -> theta (N,16): sigmoide escalonada e reducao por grupo."""
    th = TETO.to(eta.device) * torch.sigmoid(eta)
    G = G_MAT.to(eta.device)
    soma = th @ G                                        # (N,7) saida total de cada estado
    fator = torch.clamp(SAIDA_MAX / (soma + eps), max=1.0)
    return th * (fator @ G.T)                            # cada taxa recebe o fator do seu grupo

# ==== CELULA: M1 rede
class RedeM1(nn.Module):
    """g_phi: MLP + efeitos de hospital (B_hosp) e de regiao (B_reg)."""
    def __init__(self, n_cov, n_hosp, n_reg, largura=64, camadas=2, ativ=nn.SiLU):
        super().__init__()
        mods, d = [], n_cov
        for _ in range(camadas):
            mods += [nn.Linear(d, largura), ativ()]; d = largura
        mods += [nn.Linear(d, K)]
        self.mlp = nn.Sequential(*mods)
        self.B_hosp = nn.Embedding(n_hosp, K); nn.init.zeros_(self.B_hosp.weight)
        self.B_reg = nn.Embedding(n_reg, K);   nn.init.zeros_(self.B_reg.weight)
    def eta(self, z, h, reg):
        return self.mlp(z) + self.B_hosp(h) + self.B_reg(reg)
    def forward(self, z, h, reg):
        return limita_taxas(self.eta(z, h, reg))
    def penalidade(self, g_phi=1e-5, g_hosp=1e-3, g_reg=1e-3):
        p_phi = sum((w ** 2).sum() for n, w in self.mlp.named_parameters() if 'weight' in n)
        return g_phi * p_phi + g_hosp * (self.B_hosp.weight ** 2).sum() + g_reg * (self.B_reg.weight ** 2).sum()

# ==== CELULA: S1 matriz
def matriz_A(th, ec):
    """A(theta, EC): (N,7,7), coluna = estado de origem, linha = destino. ec em 1..4."""
    N = th.shape[0]; ar = torch.arange(N, device=th.device)
    gam, muE = th[:, 0], th[:, 1]
    mu, p, r = th[:, 2:6], th[:, 6:9], th[:, 9:13]
    rho, muQ, muR = th[:, 13], th[:, 14], th[:, 15]
    A = th.new_zeros(N, NS, NS)
    A[:, E, E] = 1 - gam - muE
    if FASE:                                             # inicio do tratamento -> fase inicial T -> z_EC
        A[:, T, E] = gam
        A[:, T, T] = 1 - th[:, IX['kappa']] - th[:, IX['mu_T']]
        A[ar, ec, T] = th[:, IX['kappa']]
    else:
        A[ar, ec, E] = gam                               # E -> z_EC
    if VIGIL:
        nu, dl, muV = th[:, IX['nu']], th[:, IX['delta']], th[:, IX['mu_V']]
        A[:, E, E] = 1 - gam - muE - nu
        A[:, V, E] = nu                                  # E -> V (nao tratar agora)
        A[:, V, V] = 1 - dl - muV
        if FASE: A[:, T, V] = dl                         # V -> T (tratamento tardio)
        else: A[ar, ec, V] = dl                          # V -> z_EC
    for j in range(4):
        pj = p[:, j] if j < 3 else 0.0
        A[:, Z1 + j, Z1 + j] = 1 - mu[:, j] - pj - r[:, j]
        if j < 3:
            A[:, Z1 + j + 1, Z1 + j] = p[:, j]            # z_j -> z_{j+1}
        A[:, Q, Z1 + j] = r[:, j]                         # z_j -> Q
    A[:, Q, Q] = 1 - muQ - rho
    A[ar, ec, Q] = rho                                   # Q -> z_EC (recidiva)
    A[:, R, R] = 1 - muR
    return A

def vetor_m(th):
    """m = (mu_E, mu_1..mu_4, mu_Q, mu_R): taxa de obito de cada estado."""
    c = [th[:, 1], th[:, 2], th[:, 3], th[:, 4], th[:, 5], th[:, 14], th[:, 15]] + \
        ([th[:, IX['mu_V']]] if VIGIL else []) + ([th[:, IX['mu_T']]] if FASE else [])
    return torch.stack(c, 1)

D_VEC = torch.tensor([0., 0, 0, 0, 0, -1, 1] + [0.] * (NS - 7))           # d = (0,0,0,0,0,-1,+1)

def simula_xi(th, ec, Dc, T):
    """Trajetoria nao condicionada xi(0..T): (N, T+1, 7)."""
    N = th.shape[0]; A = matriz_A(th, ec); d = D_VEC.to(th.device)
    x = th.new_zeros(N, NS); x[:, E] = 1.0
    xs = [x]
    for t in range(1, T + 1):
        x = (A @ x.unsqueeze(-1)).squeeze(-1)
        g = x[:, Q] * (Dc == t)                          # transferencia exata Q -> R em D_c
        x = x + g.unsqueeze(1) * d
        xs.append(x)
    return torch.stack(xs, 1)

def saidas_paciente(th, xi):
    """h_n(tau) = (O, R, A) e S(tau). O(0)=0."""
    m = vetor_m(th)
    S = xi.sum(-1)
    O = torch.cat([xi.new_zeros(xi.shape[0], 1), (xi[:, :-1] * m.unsqueeze(1)).sum(-1)], 1)
    Rr = xi[..., R]
    Aa = xi[..., E] + xi[..., Z1:Z4 + 1].sum(-1) + xi[..., Q] + (xi[..., V] if VIGIL else 0) + (xi[..., T] if FASE else 0)
    return S, O, Rr, Aa

# ==== CELULA: simulador
def simula_coorte(th, ec, Dc, t_diag, T_total=T_TOTAL, perda_mensal=0.005, rng=None):
    """Simulador estocastico de pacientes com o MESMO modelo de 7 estados.
    Gera os registros como o RHC/SP os guarda: data do tratamento, data da ULTIMA
    recidiva (sobrescrita), ultima informacao, obito e situacao na ultima informacao."""
    rng = rng or np.random.default_rng(SEED)
    th_ = th.detach().cpu().numpy(); ec_ = ec.cpu().numpy(); Dc_ = Dc.cpu().numpy()
    A = matriz_A(th.detach().cpu(), ec.cpu()).numpy(); m = vetor_m(th.detach().cpu()).numpy()
    N = th_.shape[0]; ar = np.arange(N)
    # censura: fim administrativo (mai/2023) ou perda de seguimento
    c_adm = T_total - t_diag
    c_perda = rng.geometric(perda_mensal, N) if perda_mensal > 0 else np.full(N, 10 ** 6)
    cens = np.minimum(c_adm, c_perda)
    s = np.zeros(N, int)                                 # todos comecam em E
    vivo = np.ones(N, bool)
    t_trat = np.zeros(N, int); t_rec = np.zeros(N, int); t_obito = np.zeros(N, int)
    estado_obito = np.full(N, -1)
    estado_fim = np.full(N, -1)
    for t in range(1, int(cens.max()) + 1):
        obs = vivo & (t <= cens)
        if not obs.any(): break
        P = A[ar, :, s]                                  # (N,7) prob. de ir para cada estado
        pm = m[ar, s]                                    # prob. de obito
        u = rng.random(N)
        cum = np.cumsum(np.concatenate([P, pm[:, None]], 1), 1)
        novo = (u[:, None] > cum).sum(1)                 # 0..NS-1 estado, NS = obito
        novo = np.minimum(novo, NS)
        morre = obs & (novo == NS)
        t_obito[morre] = t; estado_obito[morre] = s[morre]; vivo[morre] = False
        muda = obs & ~morre
        ns = np.where(muda, novo, s)
        t_trat[muda & ((s == E) | (s == V)) & (((ns >= Z1) & (ns <= Z4)) | (ns == T))] = t
        t_rec[muda & (s == Q) & (ns >= Z1) & (ns <= Z4)] = t   # sobrescreve: fica a ultima
        ns = np.where(muda & (ns == Q) & (t == Dc_), R, ns)    # remissao administrativa
        s = ns
        fim = vivo & (t == cens)
        estado_fim[fim] = s[fim]
    d_obito = (t_obito > 0).astype(int)
    tau = np.where(d_obito == 1, t_obito, cens)
    ultinfo = np.where(d_obito == 1,
                       np.where(np.isin(estado_obito, [Q, R]), 'obito_outra', 'obito_cancer'),
                       np.where(np.isin(estado_fim, [Q, R]), 'vivo_sem_cancer', 'vivo_com_cancer'))
    return pd.DataFrame(dict(t_diag=t_diag, tau=tau, d_obito=d_obito,
                             t_trat=t_trat, d_trat=(t_trat > 0).astype(int),
                             t_rec=t_rec, d_rec=(t_rec > 0).astype(int),
                             ultinfo=ultinfo, EC=ec_, Dc=Dc_,
                             c_pot=t_diag + cens))   # censura potencial (so conhecida na simulacao)

# ==== CELULA: L1 forward
GRUPO_ULTINFO = {'vivo_sem_cancer': [Q, R], 'vivo_com_cancer': [E, Z1, Z2, Z3, Z4] + ([V] if VIGIL else []) + ([T] if FASE else [])}

def tensores_eventos(df, nivel=2, dev=DEV):
    """Converte a tabela de eventos em tensores.
    nivel 1: so obito/censura; nivel 2: + datas de tratamento e recidiva;
    nivel 3: + situacao na ultima informacao (IA-10)."""
    t = lambda c: torch.as_tensor(df[c].to_numpy().copy(), device=dev)
    D = dict(tau=t('tau').long(), d_obito=t('d_obito').bool(), Dc=t('Dc').long(),
             t_trat=t('t_trat').long(), d_trat=t('d_trat').bool(),
             t_rec=t('t_rec').long(), d_rec=t('d_rec').bool())
    D['usa_trat'] = D['usa_rec'] = (nivel >= 2)
    mask = torch.ones(len(df), 7, device=dev)
    if nivel >= 3:
        for k, est in GRUPO_ULTINFO.items():
            sel = torch.as_tensor((df['ultinfo'] == k).to_numpy(), device=dev)
            mk = torch.zeros(7, device=dev); mk[est] = 1
            mask[sel] = mk
    D['grupo_vivo'] = mask
    return D

def log_verossimilhanca(th, ec, D):
    """log L_n pelo algoritmo forward escalonado (Bloco L1)."""
    N = th.shape[0]; dev = th.device
    A = matriz_A(th, ec); m = vetor_m(th); d = D_VEC.to(dev)
    um_ec = torch.nn.functional.one_hot(ec, NS).to(th.dtype)
    gam, rho = th[:, 0:1], th[:, 13:14]
    tau, dob = D['tau'], D['d_obito']
    alpha = th.new_zeros(N, NS); alpha[:, E] = 1.0
    logc = th.new_zeros(N); logL = th.new_zeros(N)
    for t in range(1, int(tau.max()) + 1):
        # obito no mes t: P = m' alpha(t-1)
        morre = (t == tau) & dob
        pm = (m * alpha).sum(1).clamp_min(1e-300)
        logL = torch.where(morre, logc + torch.log(pm), logL)
        x = (A @ alpha.unsqueeze(-1)).squeeze(-1)
        aE, aQ = alpha[:, E:E + 1], alpha[:, Q:Q + 1]
        if D['usa_trat']:
            antes = ((t < D['t_trat']) | ~D['d_trat']).unsqueeze(1)
            x = x - antes * gam * aE * um_ec                     # anula E -> z antes do tratamento
            x = torch.where(((t == D['t_trat']) & D['d_trat']).unsqueeze(1), gam * aE * um_ec, x)
        if D['usa_rec']:
            depois = ((t > D['t_rec']) | ~D['d_rec']).unsqueeze(1)
            x = x - depois * rho * aQ * um_ec                    # anula Q -> z depois da ultima recidiva
            x = torch.where(((t == D['t_rec']) & D['d_rec']).unsqueeze(1), rho * aQ * um_ec, x)
        g = x[:, Q] * (D['Dc'] == t)
        x = x + g.unsqueeze(1) * d                               # transferencia Q -> R em D_c
        c = x.sum(1).clamp_min(1e-300)
        ativo = t <= tau
        logc = logc + torch.where(ativo, torch.log(c), torch.zeros_like(c))
        alpha = torch.where(ativo.unsqueeze(1), x / c.unsqueeze(1), alpha)
        vivo_fim = (t == tau) & ~dob
        pv = (alpha * D['grupo_vivo']).sum(1).clamp_min(1e-300)
        logL = torch.where(vivo_fim, logc + torch.log(pv), logL)
    return logL

# ==== CELULA: S2 superposicao
def superposicao(th, ec, Dc, t_diag, cens, T_total=T_TOTAL, lote=20000):
    """y_hat(t) = sum_n h_n(t - t_n) I[t <= c_n], com c_n = t_n + tau_n (mes calendario)."""
    yO = torch.zeros(T_total + 1); yR = torch.zeros(T_total + 1); yA = torch.zeros(T_total + 1)
    for i in range(0, th.shape[0], lote):
        sl = slice(i, i + lote)
        Hmax = int((cens[sl] - t_diag[sl]).max())
        xi = simula_xi(th[sl], ec[sl], Dc[sl], Hmax)
        _, O, Rr, Aa = saidas_paciente(th[sl], xi)
        for tau in range(Hmax + 1):
            tc = t_diag[sl] + tau
            ok = (tc <= cens[sl]) & (tc <= T_total)
            yO.index_add_(0, tc[ok].cpu(), O[ok, tau].cpu())
            yR.index_add_(0, tc[ok].cpu(), Rr[ok, tau].cpu())
            yA.index_add_(0, tc[ok].cpu(), Aa[ok, tau].cpu())
    return pd.DataFrame(dict(O=yO.numpy(), R=yR.numpy(), A=yA.numpy()))

def series_observadas(df, T_total=T_TOTAL):
    """Series reconstruidas da coorte: obitos no mes t e vivos acompanhados no mes t (A + R)."""
    fim = (df.t_diag + df.tau).to_numpy()
    morto = df.d_obito.to_numpy() == 1
    O = np.bincount(fim[morto], minlength=T_total + 2)[:T_total + 1]
    ultimo_vivo = fim - morto                       # quem morre em t nao esta vivo em t
    ent = np.bincount(df.t_diag, minlength=T_total + 2)[:T_total + 1]
    sai = np.bincount(np.minimum(ultimo_vivo + 1, T_total + 1), minlength=T_total + 2)[:T_total + 1]
    return pd.DataFrame(dict(O=O, vivos=np.cumsum(ent) - np.cumsum(sai)))

# ==== CELULA: L2 metricas
def wape(y, yhat):
    y, yhat = np.asarray(y), np.asarray(yhat)
    return np.abs(y - yhat).sum() / max(np.abs(y).sum(), 1e-12)

def kaplan_meier(tau, d, H):
    S, s = np.ones(H + 1), 1.0
    for t in range(1, H + 1):
        n = (tau >= t).sum(); k = ((tau == t) & (d == 1)).sum()
        if n > 0: s *= 1 - k / n
        S[t] = s
    return S

def c_index(tau, d, risco, max_n=5000, rng=None):
    """C-index de Harrell (amostra de ate max_n pacientes)."""
    rng = rng or np.random.default_rng(SEED)
    idx = rng.choice(len(tau), min(max_n, len(tau)), replace=False)
    t, e, r = tau[idx], d[idx], risco[idx]
    comp = (t[:, None] < t[None, :]) & (e[:, None] == 1)
    conc = (r[:, None] > r[None, :]) & comp
    emp = (r[:, None] == r[None, :]) & comp
    return (conc.sum() + 0.5 * emp.sum()) / comp.sum()

# ==== CELULA: treino
def treina(rede, Z, h, reg, ec, D, idx_tr, idx_va, epocas=500, lote=4096, lr=3e-3,
           paciencia=25, eps_val=1e-4, eps_grad=1e-5, eps_tol=1e-6, verbose=10):
    """AdamW + decaimento cossenoidal + criterios de parada da Secao 5."""
    opt = torch.optim.AdamW(rede.parameters(), lr=lr, weight_decay=0.0)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epocas)
    sub = lambda Dd, i: {k: (v[i] if torch.is_tensor(v) else v) for k, v in Dd.items()}
    melhor, estado, sem_melhora, estag, L_ant = np.inf, None, 0, 0, None
    hist = []
    for ep in range(epocas):
        rede.train(); perm = idx_tr[torch.randperm(len(idx_tr))]; L_ep = 0.0
        for i in range(0, len(perm), lote):
            b = perm[i:i + lote]
            th = rede(Z[b], h[b], reg[b])
            loss = -log_verossimilhanca(th, ec[b], sub(D, b)).mean() + rede.penalidade()
            opt.zero_grad(); loss.backward(); opt.step()
            L_ep += loss.item() * len(b) / len(perm)
        sch.step()
        gnorm = math.sqrt(sum((p.grad ** 2).sum().item() for p in rede.parameters() if p.grad is not None))
        rede.eval()
        with torch.no_grad():
            L_va = -log_verossimilhanca(rede(Z[idx_va], h[idx_va], reg[idx_va]), ec[idx_va], sub(D, idx_va)).mean().item()
        hist.append((L_ep, L_va))
        if verbose and ep % verbose == 0:
            print(f'epoca {ep:3d}  treino {L_ep:.5f}  validacao {L_va:.5f}  |grad| {gnorm:.2e}')
        if L_va < melhor - eps_val:
            melhor, sem_melhora = L_va, 0
            estado = {k: v.clone() for k, v in rede.state_dict().items()}
        else:
            sem_melhora += 1
        estag = estag + 1 if (L_ant is not None and abs(L_ep - L_ant) / max(1, abs(L_ep)) < eps_tol) else 0
        L_ant = L_ep
        motivo = ('parada antecipada' if sem_melhora >= paciencia else
                  'gradiente estacionario' if gnorm < eps_grad else
                  'estagnacao do custo' if estag >= 10 else None)
        if motivo:
            print(f'parou na epoca {ep}: {motivo}'); break
    rede.load_state_dict(estado)
    return pd.DataFrame(hist, columns=['treino', 'validacao'])

# ==== CELULA: censura potencial
def censura_potencial(df, T_total=T_TOTAL, rng=None):
    """c_n para a superposicao. Censurados: t_n + tau_n. Obitos: a censura potencial nao e
    observada; sorteia-se da distribuicao da perda de seguimento (Kaplan-Meier reverso),
    condicionada a ser posterior ao obito e limitada ao fim administrativo."""
    rng = rng or np.random.default_rng(SEED)
    tau, d = df.tau.to_numpy(), df.d_obito.to_numpy()
    adm = T_total - df.t_diag.to_numpy()
    perda = (d == 0) & (tau < adm)                       # censura antes do fim administrativo
    H = int(tau.max())
    haz = np.zeros(H + 2)
    for t in range(1, H + 1):
        n = (tau >= t).sum()
        if n: haz[t] = ((tau == t) & perda).sum() / n
    Lc = -np.cumsum(np.log1p(-np.minimum(haz, 1 - 1e-12)))   # -log G(t), nao decrescente
    alvo = Lc[np.minimum(tau, H + 1)] - np.log(rng.random(len(tau)))
    t_perda = np.searchsorted(Lc, alvo, side='left')             # primeiro t com G(t)/G(tau) < u
    c = np.where(d == 0, tau, np.minimum(t_perda, adm)).astype(int)
    return df.t_diag.to_numpy() + c
