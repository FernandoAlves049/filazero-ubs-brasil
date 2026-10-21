# Validação — FilaZero UBS Brasil

## Investigação

Execução original com falha: https://github.com/FernandoAlves049/filazero-ubs-brasil/actions/runs/39604751931
Job `119238430978`: HTTP 404 em `find_source`, na consulta ao catálogo, antes do download. Histórico examinado: commits `29ab9e4`, `9176e16`, `7c07ed3`, `2e071f1`, `29c1d6c`.

Causas adicionais corrigidas: UF numérica não reconhecida; município disponível somente como código IBGE; longitude com vírgula; expressão de acentos incorreta; `const marker = marker(...)` provocando erro de inicialização; fallback silencioso para dados comunitários; commit por GITHUB_TOKEN sem nova publicação automática.

## Dados oficiais observados em 21/10/2026

ZIP nacional: 48.024 registros, 27 UFs. Esquema real: CNES, UF, IBGE, NOME, LOGRADOURO, BAIRRO, LATITUDE, LONGITUDE. Coordenadas preservadas sem inventar geolocalização: 44.006 dentro da malha municipal; 2.097 fora da malha simplificada e 1.921 ausentes/inválidas ficam só na lista. O SHA-256 e a atualização da fonte constam em `dados/meta.json`.

| Município | Registros | Marcadores elegíveis | Só na lista |
|---|---:|---:|---:|
| Morrinhos/GO | 16 | 15 | 1 |
| Goiânia/GO | 107 | 92 | 15 |
| Caldas Novas/GO | 22 | 22 | 0 |
| Brasília/DF | 212 | 200 | 12 |
| São Paulo/SP | 652 | 538 | 114 |

## Testes e evidências

- 10 testes unitários Python executados localmente com sucesso: esquema numérico, zeros do CNES, decimal com vírgula, coordenadas ausentes/externas, números não finitos, município desconhecido, UF divergente, CNES inválido, código legado DF, polígonos com buracos e fallback de catálogo.
- `scripts/validar_dados.py`: cobertura das 27 UFs, total, unicidade, invariantes das coordenadas e cinco cidades. Resultado: `evidencias/dados.json`.
- `node --check assets/app.js`: aprovado.
- `tests/browser.cjs`: teste real Chromium, desktop e viewport mobile; cinco cidades (inclui buscas sem acentos), lista/marcadores, overflow horizontal, seleção, vagas/duplicidade, prioridades, fila esgotada, persistência, reset, indicadores, ausência de POST, mapa bloqueado, localStorage inválido e 503 com recuperação.
- A instalação local do navegador falhou no download do binário (arquivo inválido). A execução do navegador será comprovada pelo relatório `browser.json` e capturas do workflow, nunca inferida dos testes Python.
- Os workflows preservam relatórios e capturas como artefatos. O Pages só publica depois que os testes passam.

## Funcionalidade real, simulada e pendente

Real: dados públicos CNES, busca nacional por município/UF, validação territorial IBGE e mapa OpenFreeMap.

Simulada: agenda, pacientes A/B/C, prioridade, confirmação e indicadores. Nenhuma integração de atendimento, mensagem, prontuário ou paciente real. Nenhum endpoint de escrita: estado somente no navegador.

Limitações: malha simplificada pode excluir pontos próximos da fronteira; coordenada dentro do município não comprova posição exata; base oficial pode conter denominações distintas de UBS e cadastros desatualizados. O registro sem nome é identificado pelo CNES. Ceilândia com código legado é agregada a Brasília, com código original preservado. Internet/WebGL necessários para mapa. Emulação mobile não equivale a dispositivo físico/Safari. Não existe backend de agendamento real.

## Estado da publicação

Importação concluída com sucesso: [run 39607255744](https://github.com/FernandoAlves049/filazero-ubs-brasil/actions/runs/39607255744), commit do importador `d82f579e3689e96389f31e3ed70c13f099fb5c2a`, dados gerados `30d29150dac2287c18e18b1488d753c3a1233912`.

Interface publicada pelo [run 39607451516](https://github.com/FernandoAlves049/filazero-ubs-brasil/actions/runs/39607451516), commit `31a67e07550ed0b952a94f631a82248ff61de2af`. Testes Chromium desktop/mobile passaram com zero exceções JavaScript e sem requisições de escrita. HTTP 200 confirmado para página, metadados, relatório e capturas.

As primeiras capturas foram obtidas durante movimento do mapa; o teste foi reforçado para esperar todos os tiles e o fim do movimento em cada cidade, além de repetir toda a suíte no endereço público após deploy. Os resultados dessa rodada ficam no artefato `evidencias-site-publicado` da execução correspondente.

O navegador remoto da sessão possui WebGL desabilitado: usado para comprovar degradação graciosa, lista e simulação. A renderização de mapa foi testada em Chromium no Actions com renderização por software. Não foi feito teste em aparelho físico.


## Conclusão verificada

Em 21/10/2026, a execução [39607839436](https://github.com/FernandoAlves049/filazero-ubs-brasil/actions/runs/39607839436), commit `6e6d31f3df65396e495b7a99ff151f915aae6a9e`, concluiu com **sucesso**: testes Python, dados nacionais, navegador desktop/mobile, implantação e repetição da suíte no **endereço público**. Os dez cenários cidade×viewport retornaram `mapLoaded: true`, contagens e marcadores correspondentes à base, sem overflow horizontal e sem exceções JavaScript.

- [Aplicativo público](https://fernandoalves049.github.io/filazero-ubs-brasil/)
- [Resultado da suíte no site publicado](evidencias/publicado.json)
- [Artefato com capturas das cinco cidades e simulação, desktop/mobile](https://github.com/FernandoAlves049/filazero-ubs-brasil/actions/runs/39607839436/artifacts/12348617800)
- [Captura do mapa de Morrinhos](https://fernandoalves049.github.io/filazero-ubs-brasil/docs/evidencias/desktop-morrinhos.png)
- [Captura mobile](https://fernandoalves049.github.io/filazero-ubs-brasil/docs/evidencias/mobile-morrinhos.png)

Também foi feita interação manual no navegador remoto com as cinco buscas, liberação de vaga e confirmação para Paciente B. O aviso “Nenhuma mensagem foi enviada” permaneceu visível. Esse navegador sem WebGL manteve listas e simulação operacionais.

**Pendências não bloqueantes:** teste físico Android/iOS/Safari; garantia da precisão de cada endereço exige confirmação pela unidade; nenhuma integração real de agendas/pacientes foi implementada. Há também o fluxo legado `pages build and deployment` herdado nas configurações do repositório, além do workflow customizado; o workflow customizado foi o responsável pela implantação com evidências validada aqui. A exigência de testes antes da publicação vale para o workflow customizado, não constitui proteção de branch contra alterações manuais.

Nenhum erro crítico do aplicativo observado nos cenários executados. Esse resultado não constitui garantia de ausência de defeitos em navegadores ou condições não testados. Artefatos do Actions têm retenção até 19/01/2027; o JSON de resultado fica versionado no repositório.
