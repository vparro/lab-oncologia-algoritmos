# Artigo 2 (modelo caixa-cinza): pacote de testes de estresse para o cluster

Este pacote treina e avalia o modelo de 7 estados com taxas moduladas por paciente (RedeM2, custo híbrido) para cada câncer, muitas vezes, variando o que pode mudar a conclusão: a divisão dos dados, a semente, os hiperparâmetros W e L, o período de treino, os componentes do modelo e a amostra de pacientes. Cada rodada também recalcula os cenários contrafactuais, de modo que no fim temos, para cada cenário, um intervalo de confiança e uma ideia de quanto ele depende das escolhas do modelo.

O código é o mesmo que rodou aqui para os cinco cânceres (rodada base). Para mama e próstata, o código detectou D = 126 meses sozinho (ver "Regra da remissão").

## 1. Dados (já incluídos)

A pasta `dados/` já traz tudo o que as rodadas usam, para os cinco cânceres:

```
dados/<cancer>/  <cancer>_v2.csv   <cancer>.csv (quando existe)   Predições/predicoes_ec{1..4}.xlsx   Kaplan-Meier/   <prefixo>_ec{1..4}.xlsx
```

- `*_v2.csv`: tabela por paciente (RHC/SP, FOSP, anonimizada). São dados individuais: devem ficar só na área do usuário no cluster, sem cópia para áreas compartilhadas.
- `<cancer>.csv`: versão da tabela sobre a qual as predições do ML foram geradas; o código alinha as predições por chave (instituição, idade, datas, CEP, morfologia, topografia). Encontrou 22.856 de 22.865 pacientes em colo do útero, 106.895 de 107.140 em mama e 84.671 de 84.677 em próstata.
- `*_ec{1..4}.xlsx`: séries de coorte do Artigo 1, usadas para detectar a regra da remissão e conferir as séries reconstruídas.
- Um câncer entra na rodada quando o seu `<cancer>_v2.csv` está presente.

## 2. Instalação e teste

```bash
cd cluster_completo/artigo2_caixacinza
bash instalar.sh            # uma vez: cria ~/venv_artigo2 com PyTorch (somente CPU), pandas, openpyxl, matplotlib, tabulate
bash teste_rapido.sh        # 1 época por etapa, cada câncer presente; leva alguns minutos e roda fora do SLURM
```

O teste mostra, para cada câncer, a regra da remissão detectada (D e erro), o número de pacientes e se as predições do ML foram encontradas. Se algo falhar, é aqui que aparece.

## 3. Submissão

```bash
bash submeter.sh                       # todos os blocos, em ordem de prioridade
bash submeter.sh b1_base b3_grade      # só alguns blocos
MAXSIM=20 bash submeter.sh             # no máximo 20 tarefas simultâneas por bloco (padrão 50)
squeue -u $USER
python codigo/agrega.py                # a qualquer momento: resultados/resumo.md, todos.csv, cenarios.csv, figuras_resumo/
```

Cada tarefa grava `resultados/<bloco>/<cancer>__<rótulo>/resultado.json`. Uma tarefa já concluída é pulada se for ressubmetida, então dá para relançar um bloco interrompido sem perder nada.

## 4. Os blocos de teste (por câncer)

| Bloco | Tarefas por câncer | O que varia | Pergunta que responde |
|---|---|---|---|
| `b1_base` | 1 | nada (W = 0,1; L = 1,2), com figuras | Resultado principal do artigo |
| `b2_sementes` | 20 | 10 sementes × W ∈ {0; 0,1} | Quanto os resultados mudam só pela divisão treino/teste e pela inicialização? |
| `b3_grade` | 24 | W ∈ {0; 0,03; 0,1; 0,3; 1; 3} × L ∈ {0,6; 1,2; 2; 3} | Compromisso entre discriminação individual e aderência às séries; quanto liberdade (L) a rede precisa |
| `b4_temporal` | 8 | corte ∈ {2010; 2013; 2016; 2019} × W ∈ {0; 0,1} | O modelo treinado em coortes antigas prevê os óbitos e estoques das coortes novas? Com corte em 2019, compara os óbitos de 2020–21 com os previstos sem a pandemia (experimento natural) |
| `b5_ablacao` | 6 | sem hospital; sem região; só EC; verossimilhança nível 1 e 2; origem no diagnóstico | Quais componentes geram os efeitos dos cenários? |
| `b7_placebo` | 5 | hospital e tipo de hospital embaralhados entre pacientes | Controle negativo: se o modelo ainda mostrar efeito de CACON, ele está capturando ruído |
| `b8_regiao` | 17 | cada DRS fica de fora do treino e vira o teste | O modelo prevê óbitos e estoques de uma região que nunca viu? |
| `b6_bootstrap` | 100 | reamostragem dos pacientes de treino | Intervalos de confiança das métricas e dos cenários |
| **Total** | **181** | | **905 tarefas** para os 5 cânceres |

Cenários calculados em cada rodada (população inteira, efeito sobre óbitos de 2015 a 2022, vivos acompanhados e remissão em dez/2022, e S(60)):

1. todos atendidos em CACON; em UNACON com radioterapia; em UNACON sem radioterapia;
2. todos perto do hospital (distância no 10.º percentil);
3. **antecipação de estadiamento**: 10%, 20% e 50% dos pacientes de EC II a IV chegam um estadiamento antes;
4. início do tratamento duas vezes mais rápido (γ × 2).

Verificações feitas em toda rodada, sem novo treino:

- **Calibração por hospital:** óbitos observados até 60 meses contra os esperados pelo modelo (risco acumulado no seguimento de cada paciente), por hospital, no conjunto de teste; fração de hospitais fora do intervalo de 95% de Poisson.
- **Comparação com IPW:** diferença de S(60) entre CACON e os demais, estimada direto dos dados por ponderação pelo escore de propensão, contra a mesma diferença no cenário do modelo.
- **Placebo de troca:** cada paciente recebe o efeito de outro hospital do mesmo tipo, sorteado (5 vezes); a variação dos óbitos deveria ser perto de zero.

O cenário 3 é o que pensei como revelador entre os cânceres: a mesma intervenção aplicada a três (ou cinco) doenças com distribuições de estadiamento e letalidades muito diferentes mostra o quanto o modelo atribui ao estadiamento e o quanto às características do paciente e do hospital. O cenário 4 testa uma propriedade estrutural: no modelo, γ só define quando o paciente sai de E e entra no estado de doença, sem um benefício explícito do tratamento precoce.

## 4b. Blocos novos (18/11/2026): modelo global e estados novos

Esta atualização acrescenta dois blocos e não muda o que os blocos `b1` a `b8` calculam (com as opções padrão, o código dá a mesma divisão e o mesmo modelo de antes).

| Bloco | Tarefas | O que roda | Pergunta que responde |
|---|---|---|---|
| `b9_global` | 12 | os 5 cânceres num modelo só (`--cancer global`), com o hospital compartilhado entre cânceres e com um efeito por (câncer, hospital); rodada base e 5 sementes de cada | Um modelo único, em que o câncer funciona como seletor, ganha dos cinco modelos separados? O efeito do hospital aprendido nos outros cânceres ajuda o pulmão? |
| `b10_estados` | 5 por câncer (25) | espera por coorte (`--espera ec`), com limite próprio da espera (`--LE 3`), fase inicial do tratamento (`--fase 1`), vigilância (`--vigil 1`) e vigilância com fase | Os estados testados aqui no pulmão e na próstata ajudam nos cinco cânceres, com a mesma arquitetura? |

Como o modelo global funciona:

- **O câncer como seletor.** Cada câncer tem as suas 16 taxas de base, partindo das do Artigo 1 (deslocamentos `CA_<câncer>` fora do fator limitado da rede). A rede, os efeitos de região e, na versão `compartilhado`, os efeitos de hospital são os mesmos para todos. O EC entra por câncer (interações `EC_<e>_x_<câncer>`).
- **Mesmos pacientes de teste.** A divisão treino/validação/teste é feita dentro de cada câncer com a mesma semente dos modelos separados. Assim a rodada `global__*_base` testa nos mesmos pacientes que `b1_base`, e `global__*_s0..s4` nos mesmos que as sementes 3000 a 3004 de `b2_sementes` (W = 0,1). A comparação é direta, paciente a paciente.
- **Saída.** `resultados/b9_global/global__<variante>/<câncer>/resultado.json` traz, para cada câncer, exatamente as mesmas métricas, cenários e verificações de uma rodada separada. `resultado_global.json` traz o resumo e as taxas de base finais de cada câncer. `agrega.py` monta a tabela "Modelo global x modelos separados" no `resumo.md`.
- **Recursos.** `submeter.sh` pede 8 núcleos, 24 GB e 48 h para este bloco. Não medi o tempo com todos os pacientes: aqui, com 10% dos pacientes, 3 épocas da etapa A e 2 da B levaram 4 minutos, dos quais cerca de 2,5 minutos são a leitura dos dados. Pela soma das rodadas separadas, espero algumas horas por tarefa. O `tempo.txt` da primeira tarefa diz se o pedido pode baixar.

Opções novas de `roda.py` (valem também para um câncer só): `--espera ec`, `--LE`, `--vigil 1`, `--fase 1`, `--cancer global`, `--canceres`, `--hosp_global {compartilhado,por_cancer}` e `--frac` (amostra, só para teste).

## 5. Recursos

| Item | Valor |
|---|---|
| Tipo de nó | CPU (sem GPU) |
| Núcleos por tarefa | 4 (`--cpus-per-task=4`; o PyTorch usa as 4 threads) |
| Memória por tarefa | pedido de 8 GB; uso medido aqui: cerca de 1,3 GB |
| Tempo por tarefa | ver tabela abaixo; pedido de 8 h por segurança |
| Disco | menos de 2 GB para todos os resultados |
| Rede | só na instalação (pip) |

Tempos medidos aqui (servidor Intel Xeon 2,1 GHz, três rodadas em paralelo):

| Câncer | Pacientes | Núcleos | Tempo da rodada base | Memória |
|---|---|---|---|---|
| Colorretal | 58.037 | 2 | 34 min | 1,3 GB |
| Colo do útero | 22.540 | 1 | 17 min | 1,2 GB |
| Pulmão | 33.885 | 1 | 25 min | 1,2 GB |
| Mama | 105.992 | 2 | 60 min | não medida (pedido de 8 GB) |
| Próstata | 83.548 | 2 | 47 min | não medida (pedido de 8 GB) |

Com 4 núcleos por tarefa, espero de 10 a 45 minutos por tarefa (mama é a mais longa). O total fica em torno de 1.300 a 2.500 horas·núcleo para as 905 tarefas; com 50 tarefas simultâneas, cerca de 8 a 15 horas de parede. O `tempo.txt` de cada tarefa (se `/usr/bin/time` existir) registra a memória máxima, o que permite reduzir o pedido de 8 GB depois das primeiras tarefas. As rodadas de `b2_sementes` com W = 0 são mais curtas (não têm a etapa B).

Ordem sugerida, se a cota for limitada: `b1_base`, `b3_grade`, `b4_temporal` e `b7_placebo` primeiro (respondem às dúvidas de estrutura e de confiabilidade), depois `b8_regiao`, `b5_ablacao` e `b2_sementes`, e por último `b6_bootstrap`, que é mais da metade do custo.

## 5b. Mensagem ao responsável pelo cluster

Está em `../MENSAGEM_responsavel.md`, cobrindo os dois artigos.

## 6. Regra da remissão

Ao conferir as séries do Artigo 1 contra a tabela por paciente, encontrei que a série de remissão é reproduzida, com erro de 0,3% a 1,5% nas 12 coortes de colorretal, colo do útero e pulmão, por uma regra administrativa: o paciente conta como "em remissão" no mês t se está vivo, ainda acompanhado (t ≤ mês de DTULTINFO) e se já se passaram pelo menos D = 66 meses desde a consulta (DTCONSULT). Entradas seguem o mês de DTCONSULT e óbitos o mês de DTULTINFO. Por isso esta versão usa a consulta como origem do tempo do paciente e compara a remissão do registro com a fração viva do modelo após D meses. Para mama e próstata, o código testa D entre 54 e 140 meses contra a série de remissão e usa o melhor: D = 126, com erro de 0,49% (mama) e 0,78% (próstata). O valor e o erro aparecem no log de cada tarefa.

## 7. Arquivos

| Arquivo | Função |
|---|---|
| `codigo/dados.py` | Leitura, regra da remissão, alinhamento das predições, covariáveis, séries do registro reconstruídas |
| `codigo/core.py`, `modelo.py` | Modelo de 7 estados, simulação, verossimilhança com tratamento, recidiva e ULTINFO |
| `codigo/rede.py` | RedeM2: taxa = taxa de base × fator do paciente, com teto e^±L; deslocamentos de base por EC (espera) e por câncer (global) |
| `codigo/roda.py` | Uma rodada completa: etapa A, etapa B (custo híbrido); com `--cancer global`, os cânceres num modelo só |
| `codigo/avalia.py` | Avaliação, cenários e verificações de um câncer (chamado por `roda.py`, uma vez por câncer no modelo global) |
| `codigo/gera_tarefas.py` | Gera `tarefas/<bloco>.txt` a partir dos cânceres presentes |
| `codigo/agrega.py` | Junta tudo em `resumo.md`, CSVs e figuras |
| `slurm/tarefa.sh`, `submeter.sh` | Job arrays SLURM (uma linha da lista = uma tarefa) |
| `ini/` | Taxas do Artigo 1 de cada câncer, usadas como ponto de partida da taxa de base |
| `resultados_locais/` | Rodada base feita aqui para os cinco cânceres e um teste de pulmão com L = 3, para conferência (`python codigo/agrega.py resultados_locais`) |

Se o cluster não usar SLURM, cada linha de `tarefas/*.txt` é uma chamada independente de `python codigo/roda.py <linha>`.

Para refazer só as verificações de um modelo já treinado: `python codigo/roda.py --cancer <c> --saida <pasta> --carrega_rede <pasta_antiga>/redeB.pt` (mesma semente, mesma divisão).
