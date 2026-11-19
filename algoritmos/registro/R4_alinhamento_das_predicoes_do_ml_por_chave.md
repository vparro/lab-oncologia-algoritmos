# R4. Alinhamento das predições do ML por chave

**Família:** Registro: leitura e reconstrução dos dados  
**Origem:** Artigo 2  
**Situação:** validado (taxa de associação)

## O que faz

Liga as predições de sobrevida dos modelos de ML do grupo às linhas da tabela quando os índices não batem, por chave (hospital, idade, datas, CEP, morfologia, topografia).

## Entradas e saídas

- Entradas: predicoes_ec{1..4}.xlsx; <cancer>.csv
- Saídas: S_ml por paciente

## Onde está

- [`dados.py`: _predicoes](../../projetos/artigo2_caixacinza/codigo/dados.py#L72)

## Validação

22.856 de 22.865 (colo do útero), 106.895 de 107.140 (mama), 84.671 de 84.677 (próstata).

## Histórico

| Data | Autor | Mudança |
|---|---|---|
| 2026-11 | grupo (com apoio do Claude) | primeira versão catalogada |
