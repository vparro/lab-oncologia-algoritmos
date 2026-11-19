# Avaliacao de um cancer (executado por roda.py com exec, nas variaveis globais de roda.py).
# ---------------- avaliacao
res = dict(args=vars(a), meta=meta, colunas=cols, histA=histA, histB=histB, n=dict(treino=len(itr), val=len(iva), teste=len(ite)))
with torch.no_grad():
    th = torch.cat([rede(Z[i:i + 20000], h[i:i + 20000], rg[i:i + 20000]) for i in range(0, N, 20000)])
    Sn = torch.cat([saidas_paciente(th[i:i + 20000], simula_xi(th[i:i + 20000], ec[i:i + 20000], Dc[i:i + 20000], 120))[0] for i in range(0, N, 20000)]).numpy()
thn = th.numpy(); res['nll_val'] = nll_val(rede)
with torch.no_grad(): res['nll_teste'] = -log_vero(th[ite], ec[ite], sub(DD, ite)).mean().item()
tt_ = ite.numpy(); tcx = np.minimum(tau[tt_], 60); dcx = np.where(tau[tt_] <= 60, dob[tt_], 0)
r_g = 1 - Sn[tt_, 60]
ci = dict(caixa_cinza=c_index(tcx, dcx, r_g, max_n=8000), so_EC=c_index(tcx, dcx, ECv[tt_].astype(float), max_n=8000))
if meta['ml_disponivel']:
    r_s = 1 - Sml.iloc[tt_][60].to_numpy(); okm = ~np.isnan(r_s)
    ci['ml'] = c_index(tcx[okm], dcx[okm], r_s[okm], max_n=8000); ci['caixa_cinza_mesmos'] = c_index(tcx[okm], dcx[okm], r_g[okm], max_n=8000)
ci['porEC'] = {e: c_index(tcx[ECv[tt_] == e], dcx[ECv[tt_] == e], r_g[ECv[tt_] == e]) for e in range(1, 5) if (ECv[tt_] == e).sum() > 50}
res['cindex'] = ci; log('[aval] C-index', ci)
tab = []; ece_num = ece_den = 0
for e in range(1, 5):
    s = ECv[tt_] == e
    if s.sum() < 30: continue
    km = kaplan_meier(tau[tt_][s], dob[tt_][s], 120)
    row = dict(EC=e, n_teste=int(s.sum()), KM_teste=km[60], modelo=Sn[tt_][s, 60].mean(), KM_teste_curva=km[::6].tolist(), modelo_curva=Sn[tt_][s].mean(0)[::6].tolist())
    if meta['ml_disponivel']: row['ML'] = float(np.nanmean(Sml.iloc[tt_][s][60]))
    tab.append(row)
q = np.quantile(r_g, np.linspace(0, 1, 11)); dec = np.clip(np.searchsorted(q, r_g, side='right') - 1, 0, 9); cal = []
for k in range(10):
    s = dec == k; km = kaplan_meier(tau[tt_][s], dob[tt_][s], 60)[60]; pr = Sn[tt_][s, 60].mean()
    cal.append(dict(decil=k, previsto=pr, KM=km, n=int(s.sum()))); ece_num += s.sum() * abs(pr - km); ece_den += s.sum()
res['S60'] = tab; res['calibracao_decis'] = cal; res['ECE_S60'] = ece_num / ece_den
log('[aval] S60', [(r['EC'], round(r['KM_teste'], 3), round(r['modelo'], 3)) for r in tab], 'ECE', round(res['ECE_S60'], 4))
taxas = []
for k, nm in enumerate(NOMES_TAXAS):
    row = dict(taxa=nm)
    for e in range(1, 5):
        v = thn[ECv == e, k]
        if len(v): row[f'EC{e}'] = [float(np.quantile(v, .25)), float(np.median(v)), float(np.quantile(v, .75))]
    taxas.append(row)
res['taxas'] = taxas
yh = series_modelo(rede, Pt).numpy(); wa = {}
for j, nm in enumerate(['O', 'V', 'Rad']):
    wa[nm] = {e: float(np.abs(yh[j, e - 1] - Y[j, e - 1]).sum() / max(Y[j, e - 1].sum(), 1)) for e in range(1, 5)}
    wa[nm]['total'] = float(np.abs(yh[j].sum(0) - Y[j].sum(0)).sum() / max(Y[j].sum(), 1))
res['wape'] = wa; log('[aval] WAPE', json.dumps(wa))
if a.exclui_reg >= 0 or a.divisao == 'temporal':
    Yte = np.zeros((3, 4, TA)); itn = ite.numpy()
    for e in range(1, 5): Yte[:, e - 1] = dados.series_observadas(ev.iloc[itn][ECv[itn] == e], Dm, TA)
    yte = series_modelo(rede, ite).numpy()
    res['wape_teste'] = {nm: float(np.abs(yte[j].sum(0) - Yte[j].sum(0)).sum() / max(Yte[j].sum(), 1)) for j, nm in enumerate(['O', 'V', 'Rad'])}
    m = slice(180, 276)
    res['totais_teste'] = dict(obitos_2015_22_obs=float(Yte[0, :, m].sum()), obitos_2015_22_mod=float(yte[0, :, m].sum()),
                               vivos_dez22_obs=float(Yte[1, :, 275].sum()), vivos_dez22_mod=float(yte[1, :, 275].sum()))
    if a.divisao == 'temporal':                        # pandemia: obitos 2020-21 observados x previstos sem conhecer a pandemia
        mc = slice(242, 264); res['covid'] = dict(obs=float(Yte[0, :, mc].sum() + Y[0, :, mc].sum()), mod=float(yte[0, :, mc].sum() + yh[0, :, mc].sum()))
    log('[aval] fora da amostra', res['wape_teste'], res['totais_teste'])
dd = d.assign(S60=Sn[:, 60], faixa=pd.cut(d.IDADE, [0, 50, 65, 75, 200], labels=['<50', '50-64', '65-74', '75+']))
res['S60_hab'] = {str(k): v for k, v in dd.pivot_table(index='HABILIT_HOSP', columns='EC', values='S60', aggfunc='mean').round(4).to_dict().items()}
res['S60_idade'] = {str(k): v for k, v in dd.pivot_table(index='faixa', columns='EC', values='S60', aggfunc='mean', observed=True).round(4).to_dict().items()}
res['S60_dispersao'] = {e: [float(np.quantile(Sn[ECv == e, 60], q)) for q in (.1, .5, .9)] for e in range(1, 5) if (ECv == e).any()}

# ---------------- cenarios (populacao inteira)
NOMES_HAB = {0: 'UNACON sem radioterapia', 1: 'CACON', 2: 'UNACON com radioterapia'}
def resumo(nm, yhc, Sc, extra=None):
    m = slice(180, 276)                                 # jan/2015 a dez/2022
    r = dict(cenario=nm, obitos_2015_22=float(yhc[0, :, m].sum()), vivos_dez22=float(yhc[1, :, 275].sum()),
             remissao_adm_dez22=float(yhc[2, :, 275].sum()), R_latente_dez22=float(yhc[3, :, 275].sum()),
             S60_total=float(Sc.mean()), O_mensal=yhc[0].sum(0).tolist(), V_mensal=yhc[1].sum(0).tolist(), Rad_mensal=yhc[2].sum(0).tolist())
    for e in range(1, 5): r[f'S60_EC{e}'] = float(Sc[ECv == e].mean()) if (ECv == e).any() else None
    if extra: r.update(extra)
    return r
def S60_de(Zx=None, emb=None, ecx=None, mult=None):
    with torch.no_grad():
        out = []
        for i in range(0, N, 20000):
            sl = slice(i, i + 20000)
            thc = rede((Z if Zx is None else Zx)[sl], h[sl], rg[sl], hosp_emb=None if emb is None else emb[sl], mult=mult)
            out.append(saidas_paciente(thc, simula_xi(thc, (ec if ecx is None else ecx)[sl], Dc[sl], 60))[0][:, 60])
    return torch.cat(out).numpy()
if a.cenarios:
    todos = torch.arange(N); cen = []
    cen.append(resumo('real', series_modelo(rede, todos).numpy(), Sn[:, 60]))
    hab = d.HABILIT_HOSP.to_numpy(); Wh = rede.B_hosp.weight.detach()
    for k in (1, 2, 0):
        Zc = Z.clone()
        for j in (1, 2):
            c = f'HABILIT_HOSP_{j}'
            if c in cols: Zc[:, cols.index(c)] = float(k == j)
        emb = Wh[np.unique(hosp[hab == k])].mean(0).expand(N, -1)
        cen.append(resumo('todos em ' + NOMES_HAB[k], series_modelo(rede, todos, Zx=Zc, emb=emb).numpy(), S60_de(Zc, emb)))
    if 'dist' in cols:
        Zc = Z.clone(); Zc[:, cols.index('dist')] = float(np.quantile(Z[:, cols.index('dist')].numpy(), .1)); Zc[:, cols.index('dist_na')] = 0.
        cen.append(resumo('todos perto do hospital', series_modelo(rede, todos, Zx=Zc).numpy(), S60_de(Zc)))
    # antecipacao de estadio: fracao 'antecipa' de EC2-4 entra um estadio antes (estado z e dummies de EC)
    for fr in [float(x) for x in str(a.antecipa).split(',')]:
        rs = np.random.default_rng(7); mv = (ECv >= 2) & (rs.random(N) < fr)
        ecn = ec.clone(); ecn[torch.as_tensor(mv)] -= 1; Zc = Z.clone()
        for e in (2, 3, 4):
            c = f'EC_{e}'
            if c in cols: Zc[:, cols.index(c)] = (ecn == e).double()
            for cc in CAN[1:]:                         # modelo global: interacoes EC x cancer
                cx = f'EC_{e}_x_{cc}'
                if cx in cols: Zc[:, cols.index(cx)] = (ecn == e).double() * Z[:, cols.index(f'CA_{cc}')]
        cen.append(resumo(f'{int(round(100*fr))}% de EC2-4 um estadio antes', series_modelo(rede, todos, Zx=Zc, ecx=ecn).numpy(), S60_de(Zc, ecx=ecn), dict(n_antecipados=int(mv.sum()), fracao=fr)))
    mult = torch.ones(K); mult[0] = 2.0
    cen.append(resumo('inicio do tratamento 2x mais rapido', series_modelo(rede, todos, mult=mult).numpy(), S60_de(mult=mult)))
    res['cenarios'] = cen
    for r in cen: log(f"[cenario] {r['cenario']:42s} obitos15-22 {r['obitos_2015_22']:9.0f} vivos {r['vivos_dez22']:8.0f} Rad {r['remissao_adm_dez22']:8.0f} S60 {r['S60_total']:.3f}")
# ---------------- verificacoes de confiabilidade (sem novo treino)
if a.verifica:
    hab = d.HABILIT_HOSP.to_numpy()
    # (1) calibracao por hospital: obitos observados ate 60 meses x esperados = risco acumulado -log S(min(tau,60)) de cada paciente
    tc60 = np.minimum(tau, 60); En = -np.log(np.clip(Sn[np.arange(N), tc60], 1e-12, 1)); On = ((dob == 1) & (tau <= 60)).astype(float)
    def oe(idx, grupo):
        g = pd.DataFrame(dict(g=grupo[idx], O=On[idx], E=En[idx])).groupby('g').sum(); g = g[g.E >= 5]
        z = (g.O - g.E) / np.sqrt(g.E)
        return dict(n_grupos=len(g), OE_mediana=float((g.O / g.E).median()), OE_p10=float((g.O / g.E).quantile(.1)), OE_p90=float((g.O / g.E).quantile(.9)),
                    fora_IC95=float((z.abs() > 1.96).mean()), OE_total=float(g.O.sum() / g.E.sum()), por_grupo={str(k): [float(v.O), float(v.E)] for k, v in g.iterrows()})
    itn = ite.numpy()
    res['calib_hospital'] = dict(teste=oe(itn, hosp), todos=oe(np.arange(N), hosp), regiao_todos=oe(np.arange(N), reg))
    log('[verifica] O/E por hospital (teste):', {k: v for k, v in res['calib_hospital']['teste'].items() if k != 'por_grupo'})
    # (2) IPW: efeito de CACON sobre S(60) estimado direto dos dados, comparado com o cenario do modelo
    if 'cenarios' in res and len(np.unique(hab)) == 3:
        Tt = (hab == 1).astype(float); Xc = Z[:, [i for i, c in enumerate(cols) if not c.startswith('HABILIT')]].clone()
        Xc = torch.cat([Xc, torch.ones(N, 1, dtype=Xc.dtype)], 1); wlr = torch.zeros(Xc.shape[1], dtype=Xc.dtype, requires_grad=True)
        opt2 = torch.optim.LBFGS([wlr], max_iter=200); Ttt = torch.as_tensor(Tt)
        def fecho():
            opt2.zero_grad(); l = torch.nn.functional.binary_cross_entropy_with_logits(Xc @ wlr, Ttt) + 1e-4 * (wlr ** 2).sum(); l.backward(); return l
        opt2.step(fecho); ps = torch.sigmoid(Xc @ wlr).detach().numpy().clip(.02, .98)
        wi = np.where(Tt == 1, 1 / ps, 1 / (1 - ps)); wi = np.minimum(wi, np.quantile(wi, .99))
        def km_w(m):
            S = 1.0
            for t in range(1, 61):
                r = (tau[m] >= t); n = (wi[m] * r).sum(); k = (wi[m] * ((tau[m] == t) & (dob[m] == 1))).sum()
                if n > 0: S *= 1 - k / n
            return S
        ipw = km_w(Tt == 1) - km_w(Tt == 0); bruto = kaplan_meier(tau[Tt == 1], dob[Tt == 1], 60)[60] - kaplan_meier(tau[Tt == 0], dob[Tt == 0], 60)[60]
        cc = {x['cenario']: x for x in res['cenarios']}; w0 = (hab == 0).sum() / max((hab != 1).sum(), 1)
        mod = cc['todos em CACON']['S60_total'] - (w0 * cc['todos em UNACON sem radioterapia']['S60_total'] + (1 - w0) * cc['todos em UNACON com radioterapia']['S60_total'])
        res['ipw_cacon'] = dict(S60_diferenca_bruta=float(bruto), S60_diferenca_IPW=float(ipw), S60_diferenca_modelo=float(mod), auc_aprox=None)
        log('[verifica] CACON x demais, diferenca de S(60): bruta %.3f, IPW %.3f, modelo %.3f' % (bruto, ipw, mod))
    # (3) troca de hospital dentro do mesmo tipo: quanto o cenario depende de qual hospital, e nao do tipo
    if a.ablacao not in ('sem_hosp', 'so_EC'):
        Wh = rede.B_hosp.weight.detach(); out = []; todos = torch.arange(N)
        base = series_modelo(rede, todos).numpy()[0, :, 180:276].sum()
        for r_ in range(5):
            rs2 = np.random.default_rng(900 + r_); novo = hosp.copy()
            for k in np.unique(hab):
                hs = np.unique(hosp[hab == k]); m = hab == k; novo[m] = rs2.choice(hs, m.sum())
            emb = Wh[torch.as_tensor(novo).long()]
            out.append(float(series_modelo(rede, todos, emb=emb).numpy()[0, :, 180:276].sum() / base - 1) * 100)
        res['placebo_troca_hospital_mesmo_tipo'] = dict(d_obitos_pct=out)
        log('[verifica] trocar o hospital por outro do mesmo tipo: variacao dos obitos 2015-22 (%)', [round(x, 2) for x in out])
res['tempo_s'] = time.time() - T0
import platform
try: cpu = [l.split(':')[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')][0]
except Exception: cpu = platform.processor()
res['maquina'] = dict(no=platform.node(), cpu=cpu, threads=torch.get_num_threads(), torch=torch.__version__)
json.dump(res, open(os.path.join(a.saida, 'resultado.json'), 'w'), default=float)
np.save(os.path.join(a.saida, 'series_modelo.npy'), yh.astype(np.float32)); np.save(os.path.join(a.saida, 'series_obs.npy'), Y.astype(np.float32))
log(f'[fim] {res["tempo_s"]:.0f}s')

# ---------------- figuras (opcional)
if a.figuras:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    F = os.path.join(a.saida, 'figuras'); os.makedirs(F, exist_ok=True)
    fig, ax = plt.subplots(1, 4, figsize=(15, 3.4), sharey=True)
    for r in tab:
        x = ax[r['EC'] - 1]; m6 = np.arange(0, 121, 6)
        x.step(m6, r['KM_teste_curva'], where='post', color='k', lw=1.5, label='KM (teste)')
        x.plot(m6, r['modelo_curva'], color='tab:blue', lw=2, label='caixa-cinza')
        if 'ML' in r: x.plot([60], [r['ML']], 'D', color='tab:orange', label='ML do grupo (S60)')
        x.set_title(f"EC{r['EC']} (n teste = {r['n_teste']})"); x.set_xlabel('meses desde a consulta'); x.grid(alpha=.3)
    ax[0].set_ylabel('sobrevida'); ax[0].legend(fontsize=8); plt.tight_layout(); plt.savefig(F + '/calibracao.png', dpi=150); plt.close()
    anos = 2000 + np.arange(TA) / 12; fig, ax = plt.subplots(3, 4, figsize=(16, 9))
    for j, tit in enumerate(['óbitos no mês', 'vivos acompanhados', 'remissão (vivo ≥ D meses)']):
        for e in range(1, 5):
            x = ax[j, e - 1]; x.plot(anos, Y[j, e - 1], '.', ms=2.5, color='k', label='registro'); x.plot(anos, yh[j, e - 1], color='tab:blue', lw=1.5, label='modelo')
            x.set_title(f'EC{e}: {tit}', fontsize=10); x.grid(alpha=.3); x.axvspan(2020 + 2 / 12, 2022, color='0.9')
    ax[0, 0].legend(fontsize=7); plt.tight_layout(); plt.savefig(F + '/series.png', dpi=150); plt.close()
    if a.cenarios:
        fig, ax = plt.subplots(1, 3, figsize=(15, 3.6))
        for r in cen:
            st = dict(lw=2.2, color='k') if r['cenario'] == 'real' else dict(lw=1.2)
            ax[0].plot(anos, pd.Series(r['O_mensal']).rolling(12, min_periods=1).mean(), label=r['cenario'], **st)
            ax[1].plot(anos, r['V_mensal'], **st); ax[2].plot(anos, r['Rad_mensal'], **st)
        for x, t in zip(ax, ['óbitos no mês (média 12 meses)', 'vivos acompanhados', 'remissão administrativa']): x.set_title(t); x.grid(alpha=.3)
        ax[0].legend(fontsize=6.5); plt.tight_layout(); plt.savefig(F + '/cenarios.png', dpi=150); plt.close()
