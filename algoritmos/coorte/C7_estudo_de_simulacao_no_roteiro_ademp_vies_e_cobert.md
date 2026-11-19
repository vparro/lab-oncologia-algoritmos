# C7. Estudo de simulação no roteiro ADEMP (viés e cobertura)

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado

## O que faz

Gera séries com taxas conhecidas a partir do ajuste e mede viés, erro quadrático e cobertura dos intervalos.

## Entradas e saídas

- Entradas: taxas verdadeiras; cenários
- Saídas: viés, REQM, cobertura

## Onde está

- [`coorte.py`: serie_sintetica](../../projetos/artigo1_coorte/coorte.py#L235)
- [`coorte.py`: simulacao_vies](../../projetos/artigo1_coorte/coorte.py#L287)
- [`coorte.py`: simulacao_cobertura](../../projetos/artigo1_coorte/coorte.py#L303)

## Validação

é o próprio instrumento de validação do Artigo 1 (Morris et al., 2019).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
