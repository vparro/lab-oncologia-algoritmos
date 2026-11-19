# P3. RedeM2: taxas moduladas pelo paciente

**Família:** Modelo por paciente (Artigo 2)  
**Origem:** Artigo 2  
**Situação:** validado em uso; deslocamentos experimentais

## O que faz

Taxa = base x exp(L tanh(rede + hospital + região)), com deslocamentos de base fora do fator por estadiamento (espera) e por câncer (global), tetos por taxa e por estado.

## Entradas e saídas

- Entradas: covariáveis, hospital, região
- Saídas: taxas por paciente

## Onde está

- [`rede.py`: taxas_iniciais](../../projetos/artigo2_caixacinza/codigo/rede.py#L4)
- [`rede.py`: RedeM2](../../projetos/artigo2_caixacinza/codigo/rede.py#L8)

## Validação

Artigo 2, perguntas 1 a 3 em cinco cânceres.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
