# P1. Modelo de estados por paciente

**Família:** Modelo por paciente (Artigo 2)  
**Origem:** Artigo 2  
**Situação:** validado (estrutura); estados V e T experimentais

## O que faz

Cadeia de Markov de tempo discreto por paciente: espera E, doença ativa z1 a z4, controlada Q, cura presumida R e, opcionais, vigilância V e fase inicial T; transferência Q -> R em D.

## Entradas e saídas

- Entradas: taxas do paciente; estadiamento de entrada; D
- Saídas: ocupação xi(tau); sobrevida, óbito, remissão latente

## Onde está

- [`core.py`: matriz_A](../../projetos/artigo2_caixacinza/codigo/core.py#L71)
- [`core.py`: vetor_m](../../projetos/artigo2_caixacinza/codigo/core.py#L103)
- [`core.py`: simula_xi](../../projetos/artigo2_caixacinza/codigo/core.py#L111)
- [`core.py`: saidas_paciente](../../projetos/artigo2_caixacinza/codigo/core.py#L123)

## Validação

conservação de massa (teste); igualdade com a verossimilhança (teste P2).

Teste automático: `testes/test_artigo2_paciente.py::test_P1`

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
