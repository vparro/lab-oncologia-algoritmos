from core import *
ATIVOS=[E,Z1,Z2,Z3,Z4]+([V] if VIGIL else [])+([T] if FASE else [])
def tensores(ev, nivel=3, dev=DEV):
    t=lambda c: torch.as_tensor(ev[c].to_numpy().copy(), device=dev)
    D=dict(tau=t('tau').long(), d_obito=t('d_obito').bool(), Dc=t('Dc').long(),
           t_trat=t('t_trat').long(), d_trat=t('d_trat').bool(), t_rec=t('t_rec').long(), d_rec=t('d_rec').bool())
    D['usa_trat']=D['usa_rec']=(nivel>=2)
    if nivel<2: D['d_trat']=torch.zeros_like(D['d_trat']); D['d_rec']=torch.zeros_like(D['d_rec'])
    mv=torch.ones(len(ev),NS); mo=torch.ones(len(ev),NS)
    if nivel>=3:
        a=torch.zeros(NS); a[ATIVOS]=1
        u=torch.as_tensor(ev.ult.to_numpy())
        mv[u==1]=a          # ULTINFO 1: vivo, com cancer -> doenca ativa
        mo[u==3]=a          # ULTINFO 3: obito por cancer -> a partir de doenca ativa
    D['grupo_vivo']=mv; D['grupo_obito']=mo
    return D
def log_vero(th, ec, D):
    N=th.shape[0]; A=matriz_A(th,ec); m=vetor_m(th); d=D_VEC
    um=torch.nn.functional.one_hot(ec,NS).to(th.dtype); gam,rho=th[:,0:1],th[:,13:14]
    tau,dob=D['tau'],D['d_obito']
    alpha=th.new_zeros(N,NS); alpha[:,E]=1.; logc=th.new_zeros(N); logL=th.new_zeros(N)
    for t in range(1,int(tau.max())+1):
        morre=(t==tau)&dob
        pm=(m*alpha*D['grupo_obito']).sum(1).clamp_min(1e-300)
        logL=torch.where(morre,logc+torch.log(pm),logL)
        x=(A@alpha.unsqueeze(-1)).squeeze(-1); aE,aQ=alpha[:,E:E+1],alpha[:,Q:Q+1]
        dest=um if not FASE else torch.nn.functional.one_hot(torch.full_like(ec,T),NS).to(th.dtype)
        ent=gam*aE*dest                                     # fluxo para o tratamento no mes t
        if VIGIL: ent=ent+th[:,IX['delta']:IX['delta']+1]*alpha[:,V:V+1]*dest   # + tratamento tardio a partir de V
        antes=((t<D['t_trat'])|~D['d_trat']).unsqueeze(1)
        x=x-antes*ent
        x=torch.where(((t==D['t_trat'])&D['d_trat']).unsqueeze(1),ent,x)
        depois=((t>D['t_rec'])|~D['d_rec']).unsqueeze(1)
        x=x-depois*rho*aQ*um
        x=torch.where(((t==D['t_rec'])&D['d_rec']).unsqueeze(1),rho*aQ*um,x)
        g=x[:,Q]*(D['Dc']==t); x=x+g.unsqueeze(1)*d
        c=x.sum(1).clamp_min(1e-300); ativo=t<=tau
        logc=logc+torch.where(ativo,torch.log(c),torch.zeros_like(c))
        alpha=torch.where(ativo.unsqueeze(1),x/c.unsqueeze(1),alpha)
        vf=(t==tau)&~dob
        pv=(alpha*D['grupo_vivo']).sum(1).clamp_min(1e-300)
        logL=torch.where(vf,logc+torch.log(pv),logL)
    return logL
