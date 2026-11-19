# A6. IPW do efeito do tipo de hospital

**Família:** Avaliação e validação  
**Origem:** Artigo 2  
**Situação:** em uso; sem teste unitário

## O que faz

Escore de propensão por regressão logística (LBFGS), pesos truncados no p99 e Kaplan-Meier ponderado; compara com o cenário do modelo.

## Entradas e saídas

- Entradas: covariáveis; tratamento (CACON); eventos
- Saídas: diferença de S(60) bruta, IPW e do modelo

## Onde está

- [`avalia.py`: km_w](../../projetos/artigo2_caixacinza/codigo/avalia.py#L129)

## Validação

Artigo 2, pergunta 2.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
