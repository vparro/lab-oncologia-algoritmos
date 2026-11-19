# C2. Censura estimada com resíduo AR(1)

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado (resultado negativo documentado)

## O que faz

Variante em que o modelo gera a censura (taxa constante por coorte) e prevê o resíduo com AR(1).

## Entradas e saídas

- Entradas: taxas + kappa por coorte
- Saídas: censurados previstos

## Onde está

- [`coorte.py`: estima_phi](../../projetos/artigo1_coorte/coorte.py#L180)

## Validação

Artigo 1, critério (n): viés de S(60) de até 15 pontos; conclusão: a censura deve ser entrada.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
