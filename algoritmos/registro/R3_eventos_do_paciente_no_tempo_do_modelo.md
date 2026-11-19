# R3. Eventos do paciente no tempo do modelo

**Família:** Registro: leitura e reconstrução dos dados  
**Origem:** Artigo 2  
**Situação:** em uso; sem teste unitário

## O que faz

Converte datas em meses desde a origem (consulta ou diagnóstico): tratamento, recidiva (com piso de 2 ou 3 meses após o tratamento), óbito e censura; descarta recidivas depois de D.

## Entradas e saídas

- Entradas: tabela *_v2.csv
- Saídas: tabela ev, covariáveis padronizadas, hospital, região, meta

## Onde está

- [`dados.py`: carrega](../../projetos/artigo2_caixacinza/codigo/dados.py#L98)

## Validação

contagens conferidas no log de cada rodada.

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
