# C3. Deconvolução da sobrevida a partir das séries

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado; intervalos com subcobertura

## O que faz

Recupera a sobrevida de cada coorte das séries de entradas, óbitos e censurados, sem o modelo de estados: risco constante por faixas, máxima verossimilhança de Poisson penalizada.

## Entradas e saídas

- Entradas: entradas, óbitos, censurados
- Saídas: risco h(tau) e sobrevida S(tau)

## Onde está

- [`coorte.py`: obitos_esperados](../../projetos/artigo1_coorte/coorte.py#L133)
- [`coorte.py`: deconvolucao](../../projetos/artigo1_coorte/coorte.py#L143)
- [`coorte.py`: recupera_sobrevida](../../projetos/artigo1_coorte/coorte.py#L151)

## Validação

teste com risco exponencial conhecido; Artigo 1, critério (k): cobertura de 64% a 86%.

Teste automático: `testes/test_artigo1_coorte.py::test_C3`

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
