# P4. Custo híbrido e treino em duas etapas

**Família:** Modelo por paciente (Artigo 2)  
**Origem:** Artigo 2  
**Situação:** validado em uso

## O que faz

Etapa A: máxima verossimilhança com parada antecipada. Etapa B: verossimilhança + W x erro das séries do sistema, com gradiente das séries estimado sem viés por lote.

## Entradas e saídas

- Entradas: dados de P2 e séries de R2
- Saídas: rede treinada

## Onde está

- [`roda.py`: etapa A: verossimilhanca](../../projetos/artigo2_caixacinza/codigo/roda.py#L145)
- [`roda.py`: etapa B: custo hibrido](../../projetos/artigo2_caixacinza/codigo/roda.py#L168)

## Validação

Artigo 2; grade W x L no cluster (b3).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
