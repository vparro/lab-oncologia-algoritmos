# C1. Modelo por coorte (MC) e por estadiamento (ME)

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado

## O que faz

Sistema linear de tempo discreto com estados de doença ativa por estadiamento, controlada (Q) e remissão (R); entradas e censurados vêm das tabelas; remissão pela regra Q(D) ou S(D).

## Entradas e saídas

- Entradas: 13 taxas mensais; entradas e censurados por coorte; D
- Saídas: óbitos, remissão e estoque em tratamento por coorte; resposta impulsiva (sobrevida)

## Onde está

- [`coorte.py`: impulso](../../projetos/artigo1_coorte/coorte.py#L72)
- [`coorte.py`: simula](../../projetos/artigo1_coorte/coorte.py#L82)

## Validação

conservação de massa e não negatividade (testes); agregação exata ME = soma do MC; Artigo 1, seções de resultados e qualidade.

Teste automático: `testes/test_artigo1_coorte.py::test_C1`

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
