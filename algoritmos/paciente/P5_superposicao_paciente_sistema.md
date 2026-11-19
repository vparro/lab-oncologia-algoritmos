# P5. Superposição paciente -> sistema

**Família:** Modelo por paciente (Artigo 2)  
**Origem:** Artigo 2  
**Situação:** validado

## O que faz

Soma as trajetórias dos pacientes no calendário, por grupo (estadiamento, ou câncer x estadiamento), até a censura potencial de cada um.

## Entradas e saídas

- Entradas: rede; pacientes
- Saídas: séries O, V, Rad do modelo

## Onde está

- [`roda.py`: saidas_cal](../../projetos/artigo2_caixacinza/codigo/roda.py#L119)
- [`roda.py`: series_modelo](../../projetos/artigo2_caixacinza/codigo/roda.py#L129)

## Validação

exata por linearidade; comparada com R2 em cada rodada.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
