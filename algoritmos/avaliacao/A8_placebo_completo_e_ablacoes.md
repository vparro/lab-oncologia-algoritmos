# A8. Placebo completo e ablações

**Família:** Avaliação e validação  
**Origem:** Artigo 2  
**Situação:** em validação

## O que faz

Embaralha hospital e tipo de hospital dentro de cada câncer antes do treino; ou treina sem hospital, sem região ou só com o estadiamento.

## Entradas e saídas

- Entradas: opções --placebo e --ablacao
- Saídas: rodadas comparáveis

## Onde está

- [`roda.py`: a.placebo > 0](../../projetos/artigo2_caixacinza/codigo/roda.py#L71)
- [`roda.py`: ablacao ==](../../projetos/artigo2_caixacinza/codigo/roda.py#L68)

## Validação

resultados pendentes (cluster, b5 e b7).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
