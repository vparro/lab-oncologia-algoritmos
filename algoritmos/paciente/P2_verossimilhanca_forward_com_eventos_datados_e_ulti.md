# P2. Verossimilhança forward com eventos datados e ULTINFO

**Família:** Modelo por paciente (Artigo 2)  
**Origem:** Artigo 2  
**Situação:** validado

## O que faz

Probabilidade dos eventos de cada paciente (tratamento no mês registrado, recidiva, óbito por câncer a partir de doença ativa, vivo no fim) pelo algoritmo forward, com normalização a cada mês.

## Entradas e saídas

- Entradas: taxas; eventos; nível de informação (1 a 3)
- Saídas: log L por paciente (diferenciável)

## Onde está

- [`modelo.py`: tensores](../../projetos/artigo2_caixacinza/codigo/modelo.py#L3)
- [`modelo.py`: log_vero](../../projetos/artigo2_caixacinza/codigo/modelo.py#L17)

## Validação

soma 1 sobre os desfechos e coincide com o simulador (teste); forma fechada do paciente não tratado (teste).

Teste automático: `testes/test_artigo2_paciente.py::test_P2`

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
