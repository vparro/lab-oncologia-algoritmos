# P7. Censura potencial

**Família:** Modelo por paciente (Artigo 2)  
**Origem:** Artigo 2  
**Situação:** em uso

## O que faz

Fim de seguimento potencial de cada paciente: a data de censura, ou, para quem morreu, uma censura sorteada do Kaplan-Meier reverso.

## Entradas e saídas

- Entradas: eventos
- Saídas: mês de censura potencial

## Onde está

- [`core.py`: censura_potencial](../../projetos/artigo2_caixacinza/codigo/core.py#L327)

## Validação

usada em todas as rodadas; sem teste unitário.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
