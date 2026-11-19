# A7. Placebo de troca de hospital dentro do tipo

**Família:** Avaliação e validação  
**Origem:** Artigo 2  
**Situação:** em uso

## O que faz

Troca o hospital de cada paciente por outro do mesmo tipo, sorteado, e mede a variação dos óbitos (deveria ser quase nula).

## Entradas e saídas

- Entradas: rede treinada
- Saídas: variação dos óbitos (%) em 5 sorteios

## Onde está

- [`avalia.py`: placebo_troca_hospital_mesmo_tipo](../../projetos/artigo2_caixacinza/codigo/avalia.py#L150)

## Validação

Artigo 2, pergunta 2.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
