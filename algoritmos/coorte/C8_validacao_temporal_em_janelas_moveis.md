# C8. Validação temporal em janelas móveis

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado

## O que faz

Ajusta numa janela de W meses e prevê os h meses seguintes; compara com a persistência sazonal e com a convolução.

## Entradas e saídas

- Entradas: janelas, horizontes
- Saídas: WAPE por série e horizonte

## Onde está

- [`coorte.py`: validacao](../../projetos/artigo1_coorte/coorte.py#L332)

## Validação

Artigo 1, critérios (l) e (m).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
