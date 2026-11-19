# A2. Índice C (concordância)

**Família:** Avaliação e validação  
**Origem:** Artigo 2  
**Situação:** validado

## O que faz

Probabilidade de ordenar corretamente o risco de dois pacientes comparáveis; subamostra para N grande.

## Entradas e saídas

- Entradas: tempos, óbito, risco
- Saídas: C

## Onde está

- [`core.py`: c_index](../../projetos/artigo2_caixacinza/codigo/core.py#L276)

## Validação

teste nos extremos (1 e 0).

Teste automático: `testes/test_artigo2_paciente.py::test_A2`

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
