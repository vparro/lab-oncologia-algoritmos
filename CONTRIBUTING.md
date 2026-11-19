# Como contribuir

## Repositório do grupo e repositórios individuais

- **Este repositório (organização do laboratório)** é a fonte oficial: a versão que todos usam, que vai para os artigos e que sobrevive à saída de qualquer pessoa do grupo.
- **Cada pesquisador trabalha no seu fork** (cópia na conta pessoal) e propõe as mudanças por *pull request*. Os commits levam o nome de quem os fez e aparecem no perfil pessoal do GitHub, de modo que a produção individual fica documentada sem duplicar código.
- **Repositórios pessoais** servem para exploração que ainda não é algoritmo do grupo (testes de ideias, código de disciplina). Quando a ideia vira algoritmo usado em artigo, ela entra aqui por pull request.

## Fluxo

1. Faça um fork e crie um ramo com nome descritivo (`p3-taxas-por-ano`).
2. Altere o código, atualize o README do algoritmo (seções *Validação* e *Histórico*) e acrescente ou ajuste o teste com o ID do algoritmo.
3. Rode `python -m pytest testes`.
4. Abra o pull request descrevendo o que mudou e qual resultado de artigo pode mudar. Outra pessoa do grupo revisa antes do merge.
5. Para um artigo, marque a versão usada com uma *tag* (`artigo2-v1`) e cite-a.

## Regras

- **Nenhum dado de paciente** (tabelas do RHC/SP, predições individuais, resultados por paciente) entra no repositório. O `.gitignore` bloqueia as pastas e extensões usuais; confira antes do commit.
- Um algoritmo novo ganha um ID (próximo número da família) e um README em `algoritmos/<família>/`, a partir de qualquer README existente.
- Situação do algoritmo: **validado** só com teste automático ou verificação publicada; **em uso** se gera resultados sem teste próprio; **em validação**; **experimental**.
- Notebooks de exemplo usam dados sintéticos e são salvos executados.
- Textos e comentários em português.
