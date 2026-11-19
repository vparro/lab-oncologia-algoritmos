# Artigo 1 (modelo de coorte): pacote para o cluster (v3)

Esta versão roda as análises do Artigo 1 em **quatro combinações**:

| | Remissão Q(D) (versão do artigo) | Remissão S(D) (variante nova) |
|---|---|---|
| **A, censura como entrada** | `entrada`, Q | `entrada`, S |
| **B, censura estimada (AR)** | `ar`, Q | `ar`, S |

- **Censura A**: os censurados de cada mês vêm dos dados. **Censura B**: o modelo gera os censurados com uma taxa por coorte e um resíduo AR(1) na previsão.
- **Remissão Q(D)**: aos D meses, só a ocupação do estado de doença controlada (Q) passa a R. É a regra usada no artigo.
- **Remissão S(D)**: aos D meses, toda a massa viva da coorte (estadiamentos e Q) passa a R. É o que a reconstrução das séries a partir da tabela por paciente mostrou que o registro faz: conta como "em remissão" todo paciente vivo e acompanhado há pelo menos D meses (D = 66; 126 em mama e próstata), mesmo com doença ativa.

A pergunta da variante S é quanto as taxas de controle (r), de progressão (p) e a sobrevida mudam quando a regra do modelo passa a ser a do registro. Num teste aqui, em colorretal com censura A, a regra S ajustou as séries pior (custo 1.906 contra 1.274; os custos são comparáveis, mesma série e mesma função) e levou p1 e p2 a 3,9% e 5,7% ao mês. Por isso a variante precisa do bootstrap, das simulações e da validação, como a versão original, antes de qualquer conclusão.

## Etapas por combinação

| Script | O que faz | Tarefas |
|---|---|---|
| `slurm/01_ajuste.sh` | Estimação principal (6 partidas) | 5 |
| `slurm/02_bootstrap.sh` | Bootstrap: 5 cânceres × 25 blocos de 20 réplicas = **500 réplicas** por câncer | 125 |
| `slurm/03_vies.sh` | Simulação de viés: 5 cânceres × 5 cenários × 5 blocos de 10 séries | 125 |
| `slurm/04_cobertura.sh` | Cobertura dos IC: 5 cânceres × 30 séries (bootstrap de 50 em cada) | 150 |
| `slurm/05_validacao.sh` | Validação temporal: 5 cânceres × 5 janelas | 25 |
| | **Total por combinação** | **430** |
| | **Total (4 combinações)** | **1.720** |

Cada tarefa usa 1 núcleo e menos de 500 MB (pedido de 2 GB), e leva de 1 a 15 minutos (o ajuste de colorretal levou 2,4 min aqui). Total estimado: 150 a 300 horas·núcleo.

## Como rodar

```bash
cd cluster_completo/artigo1_coorte
bash instalar.sh                     # uma vez; cria ~/venv_coorte (numpy, scipy, pandas, openpyxl)
# teste rapido (cerca de 2 min cada):
source ~/venv_coorte/bin/activate
python rodar.py ajuste --cancer colo --censura entrada --remissao Q    # custo esperado 1274,27
python rodar.py ajuste --cancer colo --censura entrada --remissao S    # custo esperado 1905,81
# submissao:
bash submeter.sh                                     # as 4 combinacoes
VERSOES=entrada REMISSOES=S bash submeter.sh         # so uma
squeue -u $USER
python agrega.py                                     # resumo.md e CSVs por combinacao
```

Em cada combinação, as etapas 2 a 5 esperam o ajuste (etapa 1) daquela combinação (`--dependency=afterok`). Os arquivos de resultado têm o sufixo da censura e, na variante S, `_remS`: por exemplo `boot_colo_ar_0000.jsonl` e `boot_colo_ar_remS_0000.jsonl`.

## Conteúdo

| Arquivo | Função |
|---|---|
| `coorte.py` | Modelo, deconvolução, estimação, bootstrap, simulação e validação (opção `remissao` em `Dados`, ou variável `REMISSAO`) |
| `rodar.py` | Uma etapa para um câncer e uma combinação (`--censura`, `--remissao`) |
| `dados/` | As 20 planilhas de séries mensais agregadas (5 cânceres × 4 estadiamentos) |
| `slurm/` | Scripts das 5 etapas e `comum.sh` (ambiente, partição) |
| `submeter.sh` | Submete as combinações pedidas |
| `agrega.py` | Resume os resultados em `resumo.md` e CSVs, por combinação |

## O que devolver

```bash
python agrega.py
zip -r resultados_artigo1.zip resultados logs resumo.md *.csv
```
