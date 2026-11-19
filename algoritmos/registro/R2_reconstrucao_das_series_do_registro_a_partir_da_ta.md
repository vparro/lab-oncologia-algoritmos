# R2. Reconstrução das séries do registro a partir da tabela por paciente

**Família:** Registro: leitura e reconstrução dos dados  
**Origem:** Artigo 2  
**Situação:** validado

## O que faz

Gera as séries mensais de óbitos (O), vivos acompanhados (V) e remissão administrativa (Rad) a partir dos eventos de cada paciente.

## Entradas e saídas

- Entradas: eventos por paciente (t_diag, tau, d_obito), D
- Saídas: matriz 3 x T

## Onde está

- [`dados.py`: series_observadas](../../projetos/artigo2_caixacinza/codigo/dados.py#L150)

## Validação

coincide com as séries do Artigo 1 (mesmo erro de R1); teste unitário com um paciente.

Teste automático: `testes/test_artigo2_paciente.py::test_R2`

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
