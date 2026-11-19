# A1. Kaplan-Meier

**Família:** Avaliação e validação  
**Origem:** Artigo 2  
**Situação:** validado

## O que faz

Estimador de Kaplan-Meier em meses inteiros.

## Entradas e saídas

- Entradas: tempos, indicador de óbito, horizonte
- Saídas: S(t)

## Onde está

- [`core.py`: kaplan_meier](../../projetos/artigo2_caixacinza/codigo/core.py#L268)

## Validação

teste sem censura.

Teste automático: `testes/test_artigo2_paciente.py::test_A1`

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
