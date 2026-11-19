# Algoritmos do laboratório: modelagem de câncer a partir do RHC/SP

Biblioteca de algoritmos de modelagem, estimação, ciência de dados e validação usados pelo grupo nos estudos com o Registro Hospitalar de Câncer do Estado de São Paulo (RHC/SP, FOSP). Todos usam a mesma versão de cada algoritmo e a aprimoram aqui, com histórico, testes e autoria.

> **Nenhum dado de paciente entra neste repositório.** As tabelas do RHC/SP ficam na área de cada pesquisador e no cluster. Testes e notebooks usam dados sintéticos.

## O que já foi produzido

| Projeto | O que faz | Pasta | Artigo |
|---|---|---|---|
| Modelo por coorte | Modelos em espaço de estados por estadiamento (ME) e por coorte (MC) estimados a partir das tabelas mensais agregadas; deconvolução da sobrevida; bootstrap em blocos; estudo de simulação; validação temporal | [`projetos/artigo1_coorte`](projetos/artigo1_coorte) | Artigo 1: dinâmica de coortes a partir de séries tabulares |
| Modelo caixa-cinza por paciente | Modelo de estados por paciente com taxas moduladas por uma rede neural, custo híbrido (verossimilhança individual + séries do registro), avaliação em três perguntas, cenários contrafactuais, modelo global dos cinco cânceres | [`projetos/artigo2_caixacinza`](projetos/artigo2_caixacinza) | Artigo 2: modelo caixa-cinza do percurso do paciente |

Os dois artigos usam o mesmo sistema dinâmico em duas resoluções: o modelo por coorte é o campo médio do modelo por paciente. Por isso os algoritmos são diferentes (mínimos quadrados sobre séries agregadas, de um lado; verossimilhança por paciente e rede neural, de outro), mas compartilham a estrutura de estados e a validação.

## Catálogo de algoritmos

31 algoritmos em cinco famílias; cada um tem um README próprio com o que faz, entradas e saídas, onde está no código, como foi validado e a sua situação. Índice completo: [`algoritmos/README.md`](algoritmos/README.md).

| Família | Algoritmos | Artigo |
|---|---|---|
| [Registro](algoritmos/README.md#registro-leitura-e-reconstrução-dos-dados): regra da remissão e detecção de D, reconstrução das séries, eventos por paciente, alinhamento do ML, carga multicâncer | R1 a R5 | 2 (usados também para conferir o 1) |
| [Modelo por coorte](algoritmos/README.md#modelo-por-coorte-artigo-1): ME/MC, censura AR(1), deconvolução, estimação regularizada, perfil, bootstrap em blocos, ADEMP, validação temporal | C1 a C8 | 1 |
| [Modelo por paciente](algoritmos/README.md#modelo-por-paciente-artigo-2): estados por paciente, verossimilhança forward, RedeM2, custo híbrido, superposição, simulação estocástica, censura potencial, modelo global | P1 a P8 | 2 |
| [Avaliação](algoritmos/README.md#avaliação-e-validação): Kaplan-Meier, índice C, calibração, WAPE, O/E por hospital, IPW, placebos, ablações, divisões | A1 a A9 | 1 e 2 |
| [Cenários](algoritmos/README.md#cenários): contrafactuais de serviço, perfil de entrada e tempo | S1 | 2 |

Ainda não catalogados (estão no Artigo 1, mas não no pacote do cluster): autovalores e escalas de tempo, gramiano de observabilidade, informação de Fisher.

## Como usar

```bash
pip install -r projetos/artigo2_caixacinza/requirements.txt pytest
python -m pytest testes            # 10 testes, cerca de 3 s
jupyter lab notebooks              # exemplos comentados, já executados
```

Para rodar os modelos com os dados reais, siga o `LEIAME.md` de cada projeto.

## Testes e notebooks

- **`testes/`**: testes automáticos (pytest), um arquivo por artigo, cada teste com o ID do algoritmo no nome (`test_P2_...`). Eles verificam propriedades que precisam valer sempre: conservação de massa, a verossimilhança somar 1 e coincidir com o simulador, o Kaplan-Meier recuperar uma sobrevida conhecida. Rodam a cada mudança.
- **`notebooks/`**: um notebook comentado por família, com dados sintéticos e verdade conhecida, salvo executado. Servem para ensinar e para documentar a validação. Modelo: [`N01_paciente_avaliacao_sintetico.ipynb`](notebooks/N01_paciente_avaliacao_sintetico.ipynb).

## Como contribuir

Veja [`CONTRIBUTING.md`](CONTRIBUTING.md): cada pesquisador trabalha no seu fork e propõe mudanças por pull request; a autoria fica registrada nos commits e no histórico de cada algoritmo.

## Como citar

Veja [`CITATION.cff`](CITATION.cff).
