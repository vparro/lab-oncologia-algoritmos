# C4. Estimação por mínimos quadrados com regularizador de sobrevida

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado

## O que faz

Ajusta as 13 taxas às 12 séries por coorte, normalizadas pela raiz da média, mais W² vezes a distância à sobrevida recuperada (C3); região de confiança com limites, várias partidas.

## Entradas e saídas

- Entradas: séries por coorte; sobrevida de C3
- Saídas: taxas estimadas e custo

## Onde está

- [`coorte.py`: residuos](../../projetos/artigo1_coorte/coorte.py#L160)
- [`coorte.py`: estima](../../projetos/artigo1_coorte/coorte.py#L168)

## Validação

Artigo 1: viés de S(60) de -5,1 a +4,2 pontos em simulação.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
