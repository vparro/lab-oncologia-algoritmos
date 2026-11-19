# S1. Cenários contrafactuais

**Família:** Cenários  
**Origem:** Artigo 2  
**Situação:** validado em uso; intervalos pendentes (b6)

## O que faz

Recalcula o sistema com os mesmos pacientes e outra entrada: todos num tipo de hospital, todos perto do hospital, fração de EC2-4 antecipada um estadiamento, tratamento duas vezes mais rápido.

## Entradas e saídas

- Entradas: rede treinada
- Saídas: óbitos 2015-2022, vivos, remissão e S(60) por cenário

## Onde está

- [`avalia.py`: resumo](../../projetos/artigo2_caixacinza/codigo/avalia.py#L62)
- [`avalia.py`: S60_de](../../projetos/artigo2_caixacinza/codigo/avalia.py#L70)

## Validação

Artigo 2, pergunta 3; o cenário de tratamento mais rápido não pode mostrar benefício por construção.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
