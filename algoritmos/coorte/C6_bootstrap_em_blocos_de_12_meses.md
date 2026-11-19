# C6. Bootstrap em blocos de 12 meses

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado; subcobertura conhecida

## O que faz

Reamostra resíduos em blocos de 12 meses alinhados ao calendário e reestima, para intervalos de 95%.

## Entradas e saídas

- Entradas: ajuste; número de réplicas
- Saídas: réplicas das taxas e da sobrevida

## Onde está

- [`coorte.py`: residuos_bootstrap](../../projetos/artigo1_coorte/coorte.py#L221)
- [`coorte.py`: blocos](../../projetos/artigo1_coorte/coorte.py#L230)
- [`coorte.py`: bootstrap](../../projetos/artigo1_coorte/coorte.py#L266)

## Validação

Artigo 1, critério (k): cobertura de 73% a 87%, abaixo dos 95% nominais.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
