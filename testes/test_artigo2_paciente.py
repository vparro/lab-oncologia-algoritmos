"""Família P e A (Artigo 2, modelo por paciente e avaliação). Dados sintéticos."""
import numpy as np, pandas as pd, torch
import core, modelo, dados

def theta(n=3):
    th = torch.full((n, core.K), 0.02); th[:, core.IX['gamma']] = 0.4
    return th

def test_P1_simulador_conserva_massa():
    """Queda da sobrevida entre 0 e H = soma dos óbitos mensais."""
    th = theta(); ec = torch.tensor([1, 2, 4]); Dc = torch.tensor([66, 66, 66])
    xi = core.simula_xi(th, ec, Dc, 100); S, O, _, _ = core.saidas_paciente(th, xi)
    assert torch.allclose(S[:, 0] - S[:, -1], O[:, 1:].sum(1), atol=1e-8)

def _eventos(n, tau, morre):
    return dict(tau=torch.full((n,), tau), d_obito=torch.full((n,), morre), Dc=torch.full((n,), 66),
                t_trat=torch.zeros(n, dtype=torch.long), d_trat=torch.zeros(n, dtype=torch.bool),
                t_rec=torch.zeros(n, dtype=torch.long), d_rec=torch.zeros(n, dtype=torch.bool),
                usa_trat=False, usa_rec=False, grupo_vivo=torch.ones(n, core.NS), grupo_obito=torch.ones(n, core.NS))

def test_P2_verossimilhanca_soma_1_e_bate_com_o_simulador():
    """Sem tratamento possível (gamma = 0): P(óbito em t), t = 1..H, mais P(vivo em H) somam 1,
    e P(óbito em t) do algoritmo forward é igual ao óbito O(t) do simulador."""
    H = 40; th = theta(1); th[:, core.IX['gamma']] = 0.; ec = torch.tensor([2])
    p = [modelo.log_vero(th, ec, _eventos(1, t, True)).exp().item() for t in range(1, H + 1)]
    p_vivo = modelo.log_vero(th, ec, _eventos(1, H, False)).exp().item()
    assert abs(sum(p) + p_vivo - 1) < 1e-8
    xi = core.simula_xi(th, ec, torch.tensor([66]), H); _, O, _, _ = core.saidas_paciente(th, xi)
    assert np.allclose(p, O[0, 1:].numpy(), atol=1e-10)

def test_P2_paciente_nao_tratado_vivo_tem_forma_fechada():
    """Paciente sem tratamento registrado e vivo em H: fica H meses na espera, P = (1 - gamma - mu_E)^H."""
    H = 40; th = theta(1); ec = torch.tensor([2])
    p = modelo.log_vero(th, ec, _eventos(1, H, False)).exp().item()
    g, mE = th[0, core.IX['gamma']].item(), th[0, core.IX['mu_E']].item()
    assert abs(p / (1 - g - mE) ** H - 1) < 1e-8

def test_A1_kaplan_meier_sem_censura_e_a_proporcao_empirica():
    tau = np.array([1, 2, 2, 5, 8]); d = np.ones(5, dtype=int)
    S = core.kaplan_meier(tau, d, 10)
    assert abs(S[2] - 2 / 5) < 1e-12 and abs(S[8]) < 1e-12

def test_A2_indice_c_extremos():
    tau = np.arange(1, 51).astype(float); d = np.ones(50, dtype=int)
    assert core.c_index(tau, d, -tau) == 1.0          # risco maior para quem morre antes
    assert core.c_index(tau, d, tau) == 0.0

def test_R2_series_observadas_de_um_paciente():
    """Paciente que entra no mês 0 e morre no mês 10: óbito contado no mês 10; vivo e acompanhado nos meses 0 a 9."""
    ev = pd.DataFrame(dict(t_diag=[0], tau=[10], d_obito=[1]))
    O, V, R = dados.series_observadas(ev, D=5, T=20)
    assert O[10] == 1 and O.sum() == 1 and V[:10].sum() == 10 and V[10:].sum() == 0 and R[5:10].sum() == 5 and R[:5].sum() == 0
