# A9. Divisões treino/validação/teste

**Família:** Avaliação e validação  
**Origem:** Artigo 2  
**Situação:** validado

## O que faz

Aleatória 70/15/15, temporal (coortes antes de um corte), região deixada de fora e bootstrap de pacientes; feita dentro de cada câncer.

## Entradas e saídas

- Entradas: semente; tipo de divisão
- Saídas: índices de treino, validação e teste

## Onde está

- [`roda.py`: divide](../../projetos/artigo2_caixacinza/codigo/roda.py#L86)

## Validação

mesma divisão do código anterior conferida em 19/11/2026.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
