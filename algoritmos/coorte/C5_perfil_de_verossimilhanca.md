# C5. Perfil de verossimilhança

**Família:** Modelo por coorte (Artigo 1)  
**Origem:** Artigo 1  
**Situação:** validado

## O que faz

Fixa uma taxa numa grade e reestima as demais, para ver se os dados a determinam.

## Entradas e saídas

- Entradas: taxas estimadas; nome da taxa; grade
- Saídas: custo e sobrevida ao longo da grade

## Onde está

- [`coorte.py`: estima_fixo](../../projetos/artigo1_coorte/coorte.py#L193)
- [`coorte.py`: perfil](../../projetos/artigo1_coorte/coorte.py#L209)

## Validação

Artigo 1: perfis planos para a progressão (não identificável).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
