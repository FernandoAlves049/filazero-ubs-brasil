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

A preencher após observar as execuções remotas e testar o endereço público. Um commit enviado não representa conclusão.
