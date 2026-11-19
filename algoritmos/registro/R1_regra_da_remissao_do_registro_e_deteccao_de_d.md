# R1. Regra da remissão do registro e detecção de D

**Família:** Registro: leitura e reconstrução dos dados  
**Origem:** Artigo 2  
**Situação:** validado (reprodução dos dados)

## O que faz

Reproduz a série de "remissão" do RHC/SP como regra administrativa (vivo, acompanhado e com pelo menos D meses desde a consulta) e escolhe D por busca em 54 a 140 meses contra a série publicada.

## Entradas e saídas

- Entradas: tabela por paciente (DTCONSULT, DTULTINFO, EC); séries de remissão do Artigo 1
- Saídas: D (meses) e erro relativo

## Onde está

- [`dados.py`: detecta_D](../../projetos/artigo2_caixacinza/codigo/dados.py#L43)

## Validação

erro de 0,3% a 1,5% nas 12 coortes de colorretal, colo do útero e pulmão (D = 66); 0,49% e 0,78% em mama e próstata (D = 126).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
