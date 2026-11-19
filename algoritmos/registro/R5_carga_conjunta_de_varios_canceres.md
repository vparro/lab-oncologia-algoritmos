# R5. Carga conjunta de vários cânceres

**Família:** Registro: leitura e reconstrução dos dados  
**Origem:** Artigo 2  
**Situação:** experimental

## O que faz

Junta os cânceres numa tabela, com o câncer como seletor (colunas CA_), interações estadiamento x câncer e código de hospital compartilhado ou por câncer.

## Entradas e saídas

- Entradas: lista de cânceres
- Saídas: mesma saída de R3, para todos

## Onde está

- [`dados.py`: carrega_global](../../projetos/artigo2_caixacinza/codigo/dados.py#L162)

## Validação

verificado de ponta a ponta numa amostra de 10%; resultados completos pendentes (cluster, b9_global).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
