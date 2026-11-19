# A4. WAPE de séries

**Família:** Avaliação e validação  
**Origem:** Artigo 1 e 2  
**Situação:** validado

## O que faz

Erro absoluto ponderado: soma dos erros absolutos sobre a soma do observado.

## Entradas e saídas

- Entradas: série observada e modelada
- Saídas: WAPE

## Onde está

- [`core.py`: wape](../../projetos/artigo2_caixacinza/codigo/core.py#L264)
- [`coorte.py`: wape](../../projetos/artigo1_coorte/coorte.py#L330)

## Validação

definição direta; existe em duplicata nos dois projetos (unificar).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
