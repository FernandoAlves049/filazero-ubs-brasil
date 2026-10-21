# 🏥 FilaZero UBS Brasil

Protótipo do Hackathon WTMI 2026. Pesquisa UBS geolocalizadas no **OpenStreetMap**, utilizando Nominatim e Overpass, e demonstra como uma fila inteligente poderia reaproveitar consultas canceladas.

**Site (após ativação do GitHub Pages):** https://fernandoalves049.github.io/filazero-ubs-brasil/

## Uso
Abra o site no navegador do celular; pesquise por cidade e UF, escolha a UBS e teste a aba Fila inteligente. Os dados das consultas e pacientes são **fictícios** e ficam no armazenamento local do seu navegador. Não há conexão com agendas reais do SUS.

## Limitações importantes
O mapa usa dados comunitários do OpenStreetMap e não a base completa e oficial do CNES; a cobertura é parcial. Nominatim e Overpass podem limitar ou bloquear consultas. Consulte a [base oficial de UBS do Ministério da Saúde](https://dadosabertos.saude.gov.br/dataset/unidades-basicas-de-saude-ubs) quando necessário. Não insira dados pessoais reais.

## Implantação
O workflow `.github/workflows/pages.yml` tenta ativar e publicar o GitHub Pages automaticamente quando você envia alterações à branch `main`. Caso a página não seja ativada, entre em **Settings → Pages → Build and deployment → Source → GitHub Actions**, depois reexecute o workflow em **Actions**.
