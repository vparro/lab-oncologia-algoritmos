# A5. O/E por hospital com intervalo de Poisson

**Família:** Avaliação e validação  
**Origem:** Artigo 2  
**Situação:** em uso; sem teste unitário

## O que faz

Óbitos observados até 60 meses contra o risco acumulado previsto, por hospital ou região; fração fora do IC de 95%.

## Entradas e saídas

- Entradas: sobrevida prevista; eventos; grupo
- Saídas: O/E por grupo e fração fora do IC

## Onde está

- [`avalia.py`: oe](../../projetos/artigo2_caixacinza/codigo/avalia.py#L112)

## Validação

Artigo 2, pergunta 2.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
