from core import *
import json
NOMES_A1=['p_1','p_2','p_3','mu_1','mu_2','mu_3','mu_4','r_1','r_2','r_3','r_4','mu_Q','mu_R']
def taxas_iniciais(arq_json):
    """theta0 inicial: taxas do Artigo 1 (MC, entrada) do mesmo cancer + gamma, mu_E, rho."""
    a1=json.load(open(arq_json))['theta']
    return dict(gamma=0.35,mu_E=0.006,rho=0.03,nu=0.02,delta=0.02,mu_V=0.003,kappa=0.15,mu_T=0.03,**dict(zip(NOMES_A1,a1)))
class RedeM2(nn.Module):
    """Taxa do paciente = taxa de base comum x modificador do paciente.
    theta_nk = theta0_k * exp(L * tanh(f_k(x_n) + b_hosp + b_reg)), fator entre e^-L e e^L."""
    def __init__(self, n_cov, n_hosp, n_reg, ini, L=1.2, largura=64, ec_cols=None, LE=None, ca_cols=None, offC_ini=None):
        super().__init__()
        # estado de espera (E) por coorte: taxas de base de gamma e mu_E proprias de cada EC de entrada,
        # fora do fator limitado da rede (ec_cols = colunas EC_2..EC_4 de z); LE = limite proprio do fator de E
        self.ec_cols = list(ec_cols) if ec_cols else []
        # taxas com base propria por EC: as da espera e, com FASE, as da fase inicial do tratamento
        self.idx_ec = [IX['gamma'], IX['mu_E']] + ([IX['kappa'], IX['mu_T']] if FASE else [])
        self.offE = nn.Parameter(torch.zeros(max(len(self.ec_cols), 1), len(self.idx_ec)))
        self.LE = L if LE is None else LE
        # modelo global: o cancer como seletor. ca_cols = colunas CA_<cancer> de z; offC = deslocamento das K taxas
        # de base de cada cancer em relacao ao de referencia (fora do fator limitado), iniciado pelo Artigo 1
        self.ca_cols = list(ca_cols) if ca_cols else []
        self.offC = nn.Parameter(torch.as_tensor(offC_ini, dtype=torch.get_default_dtype()) if offC_ini is not None
                                 else torch.zeros(max(len(self.ca_cols), 1), K))
        self.log0=nn.Parameter(torch.log(torch.tensor([max(ini[n],1e-3) for n in NOMES_TAXAS])))
        self.mlp=nn.Sequential(nn.Linear(max(n_cov,1),largura),nn.SiLU(),nn.Linear(largura,largura),nn.SiLU(),nn.Linear(largura,K))
        nn.init.zeros_(self.mlp[-1].weight); nn.init.zeros_(self.mlp[-1].bias)
        self.B_hosp=nn.Embedding(n_hosp,K); nn.init.zeros_(self.B_hosp.weight)
        self.B_reg=nn.Embedding(n_reg,K); nn.init.zeros_(self.B_reg.weight)
        self.L=L
    def forward(self,z,h,reg,hosp_emb=None,mult=None):
        b=self.B_hosp(h) if hosp_emb is None else hosp_emb
        u=torch.tanh(self.mlp(z)+b+self.B_reg(reg))
        Lv=torch.full((K,),self.L,dtype=u.dtype); Lv[0:2]=self.LE
        m=Lv*u
        if self.ec_cols:
            off=z[:,self.ec_cols]@self.offE                    # deslocamento por EC das taxas em idx_ec
            m=m.index_add(1,torch.tensor(self.idx_ec),off)
        if self.ca_cols: m=m+z[:,self.ca_cols]@self.offC.to(z.dtype)
        th=torch.exp(self.log0+m)
        if mult is not None: th=th*mult                 # cenario: multiplica taxas (ex.: gamma x 2)
        th=torch.minimum(th,TETO)
        soma=th@G_MAT; f=torch.clamp(SAIDA_MAX/(soma+1e-8),max=1.0)
        return th*(f@G_MAT.T)
    def penalidade(self,g_phi=1e-5,g_hosp=1e-3,g_reg=1e-3):
        p=sum((w**2).sum() for n,w in self.mlp.named_parameters() if 'weight' in n)
        return g_phi*p+g_hosp*(self.B_hosp.weight**2).sum()+g_reg*(self.B_reg.weight**2).sum()
