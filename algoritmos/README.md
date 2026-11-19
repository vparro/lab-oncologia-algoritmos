# Catálogo de algoritmos

Um arquivo por algoritmo. Situação: **validado** (com teste ou verificação publicada), **em uso** (usado em resultados, sem teste próprio), **em validação** (testes rodando), **experimental**.

## Registro: leitura e reconstrução dos dados

| ID | Algoritmo | Artigo | Situação |
|---|---|---|---|
| R1 | [Regra da remissão do registro e detecção de D](../algoritmos/registro/R1_regra_da_remissao_do_registro_e_deteccao_de_d.md) | 2 | validado (reprodução dos dados) |
| R2 | [Reconstrução das séries do registro a partir da tabela por paciente](../algoritmos/registro/R2_reconstrucao_das_series_do_registro_a_partir_da_ta.md) | 2 | validado |
| R3 | [Eventos do paciente no tempo do modelo](../algoritmos/registro/R3_eventos_do_paciente_no_tempo_do_modelo.md) | 2 | em uso; sem teste unitário |
| R4 | [Alinhamento das predições do ML por chave](../algoritmos/registro/R4_alinhamento_das_predicoes_do_ml_por_chave.md) | 2 | validado (taxa de associação) |
| R5 | [Carga conjunta de vários cânceres](../algoritmos/registro/R5_carga_conjunta_de_varios_canceres.md) | 2 | experimental |

## Modelo por coorte (Artigo 1)

| ID | Algoritmo | Artigo | Situação |
|---|---|---|---|
| C1 | [Modelo por coorte (MC) e por estadiamento (ME)](../algoritmos/coorte/C1_modelo_por_coorte_mc_e_por_estadiamento_me.md) | 1 | validado |
| C2 | [Censura estimada com resíduo AR(1)](../algoritmos/coorte/C2_censura_estimada_com_residuo_ar_1.md) | 1 | validado (resultado negativo documentado) |
| C3 | [Deconvolução da sobrevida a partir das séries](../algoritmos/coorte/C3_deconvolucao_da_sobrevida_a_partir_das_series.md) | 1 | validado; intervalos com subcobertura |
| C4 | [Estimação por mínimos quadrados com regularizador de sobrevida](../algoritmos/coorte/C4_estimacao_por_minimos_quadrados_com_regularizador_.md) | 1 | validado |
| C5 | [Perfil de verossimilhança](../algoritmos/coorte/C5_perfil_de_verossimilhanca.md) | 1 | validado |
| C6 | [Bootstrap em blocos de 12 meses](../algoritmos/coorte/C6_bootstrap_em_blocos_de_12_meses.md) | 1 | validado; subcobertura conhecida |
| C7 | [Estudo de simulação no roteiro ADEMP (viés e cobertura)](../algoritmos/coorte/C7_estudo_de_simulacao_no_roteiro_ademp_vies_e_cobert.md) | 1 | validado |
| C8 | [Validação temporal em janelas móveis](../algoritmos/coorte/C8_validacao_temporal_em_janelas_moveis.md) | 1 | validado |

## Modelo por paciente (Artigo 2)

| ID | Algoritmo | Artigo | Situação |
|---|---|---|---|
| P1 | [Modelo de estados por paciente](../algoritmos/paciente/P1_modelo_de_estados_por_paciente.md) | 2 | validado (estrutura); estados V e T experimentais |
| P2 | [Verossimilhança forward com eventos datados e ULTINFO](../algoritmos/paciente/P2_verossimilhanca_forward_com_eventos_datados_e_ulti.md) | 2 | validado |
| P3 | [RedeM2: taxas moduladas pelo paciente](../algoritmos/paciente/P3_redem2_taxas_moduladas_pelo_paciente.md) | 2 | validado em uso; deslocamentos experimentais |
| P4 | [Custo híbrido e treino em duas etapas](../algoritmos/paciente/P4_custo_hibrido_e_treino_em_duas_etapas.md) | 2 | validado em uso |
| P5 | [Superposição paciente -> sistema](../algoritmos/paciente/P5_superposicao_paciente_sistema.md) | 2 | validado |
| P6 | [Simulação estocástica de pacientes](../algoritmos/paciente/P6_simulacao_estocastica_de_pacientes.md) | 2 | experimental |
| P7 | [Censura potencial](../algoritmos/paciente/P7_censura_potencial.md) | 2 | em uso |
| P8 | [Modelo global multicâncer](../algoritmos/paciente/P8_modelo_global_multicancer.md) | 2 | experimental |

## Avaliação e validação

| ID | Algoritmo | Artigo | Situação |
|---|---|---|---|
| A1 | [Kaplan-Meier](../algoritmos/avaliacao/A1_kaplan_meier.md) | 2 | validado |
| A2 | [Índice C (concordância)](../algoritmos/avaliacao/A2_indice_c_concordancia.md) | 2 | validado |
| A3 | [Calibração de S(60) por decis e ECE](../algoritmos/avaliacao/A3_calibracao_de_s_60_por_decis_e_ece.md) | 2 | em uso; sem teste unitário |
| A4 | [WAPE de séries](../algoritmos/avaliacao/A4_wape_de_series.md) | 1 e 2 | validado |
| A5 | [O/E por hospital com intervalo de Poisson](../algoritmos/avaliacao/A5_o_e_por_hospital_com_intervalo_de_poisson.md) | 2 | em uso; sem teste unitário |
| A6 | [IPW do efeito do tipo de hospital](../algoritmos/avaliacao/A6_ipw_do_efeito_do_tipo_de_hospital.md) | 2 | em uso; sem teste unitário |
| A7 | [Placebo de troca de hospital dentro do tipo](../algoritmos/avaliacao/A7_placebo_de_troca_de_hospital_dentro_do_tipo.md) | 2 | em uso |
| A8 | [Placebo completo e ablações](../algoritmos/avaliacao/A8_placebo_completo_e_ablacoes.md) | 2 | em validação |
| A9 | [Divisões treino/validação/teste](../algoritmos/avaliacao/A9_divisoes_treino_validacao_teste.md) | 2 | validado |

## Cenários

| ID | Algoritmo | Artigo | Situação |
|---|---|---|---|
| S1 | [Cenários contrafactuais](../algoritmos/cenarios/S1_cenarios_contrafactuais.md) | 2 | validado em uso; intervalos pendentes (b6) |
