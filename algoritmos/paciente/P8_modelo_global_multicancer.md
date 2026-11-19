# P8. Modelo global multicâncer

**Família:** Modelo por paciente (Artigo 2)  
**Origem:** Artigo 2  
**Situação:** experimental

## O que faz

Treina todos os cânceres num modelo, com o câncer como seletor das taxas de base; avalia cada câncer nos mesmos pacientes de teste dos modelos separados.

## Entradas e saídas

- Entradas: lista de cânceres; hospital compartilhado ou por câncer
- Saídas: um resultado por câncer + resumo

## Onde está

- [`roda.py`: GLOBAL = ](../../projetos/artigo2_caixacinza/codigo/roda.py#L57)

## Validação

verificado numa amostra de 10%; resultados pendentes (b9_global).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
