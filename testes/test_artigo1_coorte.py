"""Família C (Artigo 1, modelo por coorte). Dados sintéticos, sem dados do registro."""
import numpy as np, types
import coorte as co

TH = np.array([.02, .02, .01, .02, .03, .05, .10, .05, .04, .03, .01, .002, .001])  # p1..3, mu1..4, r1..4, muQ, muR

def dd_sintetico(U=50., C=0., D=66):
    d = types.SimpleNamespace(D=D, censura='entrada', remissao='Q', phi=np.zeros(4))
    d.U = np.full((4, co.N), U); d.C = np.full((4, co.N), C)
    return d

def test_C1_impulso_sobrevida_comeca_em_1_e_nao_cresce():
    for i in range(4):
        S, Q = co.impulso(TH, i, 120)
        assert S[0] == 1.0 and np.all(np.diff(S) <= 1e-12) and np.all(Q >= 0)

def test_C1_conservacao_de_massa_sem_censura():
    """Sem censura: vivos no fim do mês = entradas acumuladas - óbitos acumulados (regras Q e S)."""
    for regra in ('Q', 'S'):
        d = dd_sintetico(); d.remissao = regra; m = co.simula(TH, d)
        for i in range(1, 5):
            vivos = m[i]['A'] + m[i]['R']; ent = np.cumsum(d.U[i - 1]); ob = np.cumsum(m[i]['O'])
            assert np.allclose(vivos, ent - ob, rtol=1e-9, atol=1e-6), regra

def test_C1_censura_nao_deixa_estados_negativos():
    d = dd_sintetico(C=5.); m = co.simula(TH, d)
    for i in range(1, 5): assert m[i]['A'].min() >= -1e-9 and m[i]['R'].min() >= -1e-9

def test_C3_deconvolucao_recupera_sobrevida_exponencial():
    """Risco constante de 3% ao mês, 200 entradas por mês, óbitos esperados (sem ruído): S(60) volta com erro < 2 pontos."""
    h = np.full(400, .03); E = np.full(co.N, 200.); C = np.zeros(co.N)
    O = co.obitos_esperados(h, E, C, co.N)
    _, S = co.deconvolucao(E, O, C, 0, co.N - 1)
    assert abs(S[60] - (1 - .03) ** 60) < .02
