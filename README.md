# FilaZero UBS Brasil

Protótipo para o Hackathon WTMI 2026: busca nacional de estabelecimentos do conjunto oficial **Unidades Básicas de Saúde — CNES / Ministério da Saúde**, com mapa MapLibre GL JS + OpenFreeMap e demonstração local de reaproveitamento de consultas.

**Aplicativo:** https://fernandoalves049.github.io/filazero-ubs-brasil/

## O que é real e o que é simulação

| Recurso | Natureza |
|---|---|
| Nome, CNES, logradouro, bairro e coordenadas | Dados públicos do conjunto oficial de UBS |
| Nome do município e UF | Correspondência com a API de localidades do IBGE |
| Marcadores | Coordenadas CNES, somente quando dentro da malha municipal IBGE |
| Cartografia | OpenFreeMap, com atribuição OpenStreetMap; requer internet e WebGL |
| Vagas, pacientes A/B/C, prioridades, convocação e indicadores | Fictícios, somente no navegador; nenhuma mensagem é enviada |
| Agendas do SUS, triagem, prontuários, disponibilidade real | Não integrados |

Não insira dados pessoais. A aplicação não possui formulário de cadastro de pacientes nem backend de atendimento. A simulação usa `localStorage` na chave `filazero-demo-v2`; Reiniciar demonstração limpa apenas esse estado. Não há acesso ao e-SUS ou agendas reais.

## Usar

1. Informe o município e a UF. A busca aceita nomes sem acentos e oferece sugestões.
2. Confira a lista. Unidades sem coordenadas utilizáveis continuam disponíveis, com explicação.
3. Selecione uma unidade, abra **Fila inteligente**, libere uma vaga fictícia e simule a convocação.
4. Veja **Indicadores** ou reinicie a demonstração.

O nome da unidade é mantido como publicado no conjunto oficial, que pode incluir estabelecimentos com outras denominações. Não se infere horário de funcionamento, serviços, capacidade ou disponibilidade de atendimento.

## Dados e atualização

- [Catálogo do Ministério da Saúde](https://dadosabertos.saude.gov.br/dataset/unidades-basicas-de-saude-ubs)
- [ZIP oficial JSON](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/CNES/Unidades_Basicas_Saude-UBS_json.zip)
- [Localidades IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/municipios)
- [Malha municipal simplificada IBGE](https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio)

`dados/meta.json` registra fonte, horário da importação, atualização do recurso quando disponível, SHA-256 do ZIP, quantidades por UF e validação das coordenadas. `dados/municipios.json` contém o catálogo de municípios; `dados/UF.json` contém os estabelecimentos.

O importador lê os metadados Next.js do portal, com fallback explícito para o URL oficial conhecido. Não depende da rota `/api/3/action` do portal, que retornava 404. Downloads têm timeout, repetição limitada para erros transitórios, limite de tamanho e suporte a gzip. Alterações inesperadas de esquema, UF ou identificadores, perda expressiva de registros e ausência de UF interrompem a publicação.

O workflow **Atualizar dados oficiais de UBS (CNES)** roda às quartas às 07:18 UTC (04:18 em Brasília), por alteração do importador ou manualmente. Após sucesso, `workflow_run` aciona a publicação; isso evita depender de eventos `push` gerados pelo `GITHUB_TOKEN`. O Pages só é implantado depois dos gates de dados, Python e navegador. A versão anterior permanece publicada quando um gate falha.

## Desenvolvimento e testes

Requer Python 3.12+ e Node 22+ apenas no desenvolvimento/CI. O site entregue é estático.

```bash
python scripts/importar_cnes.py
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/validar_dados.py
npm ci
npx playwright install --with-deps chromium
python -m http.server 8000
# em outro terminal:
npm test
# validar a publicação:
TEST_URL=https://fernandoalves049.github.io/filazero-ubs-brasil/ npm test
```

Testes usam Chromium real, nos tamanhos 1440×1000 e 390×844, verificam as cinco cidades, acentos, contagens, marcadores, ausência de overflow, simulação, persistência, falha de mapa, estado local inválido, HTTP 503 e recuperação. Capturas e resultados ficam em `docs/evidencias/` e nos artefatos do Actions.

## Limitações

- Validação territorial não comprova precisão de endereço. A malha simplificada pode excluir pontos legítimos próximos de fronteiras municipais. Esses registros ficam na lista; não são descartados nem reposicionados.
- Município recém-criado pode não existir na edição da malha: sem geometria, nenhum marcador é inventado.
- O registro legado CNES `530040` (Ceilândia/DF) é associado a Brasília (`5300108`) para busca; o código original fica em `source_city_code`.
- Um registro sem nome recebe a descrição explícita “Estabelecimento CNES … (nome não informado)”.
- O catálogo nacional não garante que todos os estabelecimentos estejam ativos ou atendendo. Confirme informações com a unidade.
- Mapa exige acesso ao OpenFreeMap. Falha de WebGL/mapa não bloqueia lista ou simulação. Primeiro carregamento e dados exigem rede; não há modo offline completo.
- Teste mobile usa emulação de viewport/touch em Chromium; não substitui teste físico em Android/iOS/Safari.

MapLibre GL JS 4.7.1 está versionado em `assets/`, reduzindo dependência de CDN. Consulte `assets/LICENSE-maplibre.txt`.

Veja [relatório de validação](docs/VALIDACAO.md) e [resultados dos dados](docs/evidencias/dados.json).
