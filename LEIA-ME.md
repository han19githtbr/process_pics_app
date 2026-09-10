# Melhoria de Qualidade de Imagens & Banco de Imagens de Alta Qualidade

Este pacote contém **apenas os arquivos novos e alterados** para adicionar a
funcionalidade solicitada ao seu projeto `processamento-de-imagens`. A estrutura
de pastas dentro deste zip é idêntica à do seu projeto — basta copiar/mesclar
por cima da pasta do projeto (sobrescrevendo os arquivos já existentes listados
abaixo como "ALTERADO").

Leia a seção **"26. Melhoria de Qualidade de Imagens & Banco de Imagens de Alta
Qualidade"** em `GUIA.md` para a explicação científica completa da técnica.

## O que foi feito (resumo)

Foi analisado se o mesmo algoritmo do recorte de letras (binarização de Otsu +
Canny) poderia ser reaproveitado para "limpar" imagens de baixa qualidade. A
resposta é **parcialmente sim**: a etapa de "Escala Adaptativa para Texto
Pequeno" (`auto_upscale_small_text`) e a estimativa de altura de glifo foram
reaproveitadas integralmente, porque resolvem o mesmo problema físico nos dois
casos. Já a binarização preto-e-branco do segmentador NÃO foi reaproveitada,
porque ela existe justamente para descartar cor/tom (o oposto do que "limpar
uma imagem preservando-a" precisa). Por isso foram implementadas técnicas novas
e documentadas cientificamente (com fórmula, técnica e explicação de cada
etapa, exibidas tanto no app quanto no GUIA.md):

1. Diagnóstico automático (nitidez, ruído, contraste)
2. Escala adaptativa para texto pequeno/borrado (reaproveitada do segmentador)
3. Redução de ruído Non-Local Means (adaptativa)
4. Balanço de branco automático (mundo cinza)
5. Realce de contraste local CLAHE (adaptativo)
6. Nitidez adaptativa (unsharp masking)

O resultado é salvo automaticamente em uma nova área/coleção do banco de dados
chamada **Banco de Imagens de Alta Qualidade** (separada do histórico de
segmentação), com uma tela própria no frontend para visualizar, buscar e
gerenciar essas imagens.

## Arquivos NOVOS (crie estes arquivos no seu projeto)

```
backend/src/core/interfaces/image_enhancer.py
backend/src/core/models/enhance_options.py
backend/src/core/models/enhance_result.py
backend/src/core/enhancers/__init__.py
backend/src/core/enhancers/quality_enhancer.py
backend/src/core/factory/enhancer_factory.py
backend/src/api/handlers/image_enhancer_handler.py

frontend/src/types/enhance.ts
frontend/src/components/ImageEnhancer/ImageEnhancer.tsx
frontend/src/components/ImageEnhancer/ImageEnhancer.css
frontend/src/components/ImageEnhancer/index.ts
frontend/src/components/ImageBank/ImageBank.tsx
frontend/src/components/ImageBank/index.ts
```

## Arquivos ALTERADOS (sobrescreva os existentes no seu projeto)

```
backend/src/api/routes/index.py        -> novas rotas /enhance e /image-bank/*
backend/src/services/mongodb_service.py -> métodos *_enhanced_image(s)
backend/src/config/settings.py          -> MONGODB_BANK_COLLECTION_NAME

frontend/src/types/index.ts    -> agora também exporta ./enhance
frontend/src/services/api.ts   -> novas funções enhanceImage/getImageBank/etc.
frontend/src/App.tsx           -> alternador de abas Segmentador / Melhoria de Qualidade
frontend/src/styles/globals.css -> classes .app-top-nav / .app-top-nav-btn

GUIA.md -> nova seção 26 + linha nova na tabela de endpoints (seção 15) + bullet na seção 1
```

> Se você já alterou `routes/index.py`, `mongodb_service.py`, `settings.py`,
> `types/index.ts`, `api.ts`, `App.tsx` ou `globals.css` desde a versão que me
> enviou, copiar por cima vai descartar suas mudanças — nesse caso, me avise
> que gero um diff/patch em vez de arquivo completo.

## Novos endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/enhance` | Melhora a qualidade da imagem e retorna as 6 etapas + métricas |
| GET | `/api/image-bank` | Lista os últimos 20 itens salvos |
| GET | `/api/image-bank/search?q=` | Busca por nome do arquivo |
| POST | `/api/image-bank/save` | Salva manualmente uma imagem já melhorada |
| GET | `/api/image-bank/{id}` | Retorna um item específico |
| DELETE | `/api/image-bank/{id}` | Remove um item |
| DELETE | `/api/image-bank` | Limpa o banco inteiro |

A coleção do MongoDB usada é `high_quality_images` (dev) /
`high_quality_images_prod` (produção), separada da coleção de histórico de
segmentação — segue o mesmo padrão de fallback local em memória se o MongoDB
não estiver configurado/disponível.

## Verificações já feitas

- `python3 -m py_compile` em todos os arquivos Python novos/alterados: OK
- Pipeline `QualityEnhancer` testado de ponta a ponta com as 3 imagens que você
  enviou (incluindo a foto borrada) — nitidez, contraste e ruído melhoraram de
  forma mensurável e comparável (metodologia explicada na seção 26.4 do GUIA.md)
- `pytest backend/tests/` — as 25 suítes de teste já existentes continuam
  passando (nenhuma regressão)
- `npx tsc --noEmit` — sem erros de tipo
- `vite build` — build de produção concluído com sucesso

## Estilo visual

Nenhum CSS novo de layout foi necessário para a maior parte da tela: os
componentes novos reaproveitam deliberadamente as classes já existentes
(`segmenter-header`, `upload-card`, `metric-card`, `pipeline-viewer-card`,
`step-*`, `history-panel`, `history-item`, etc.) definidas em
`Segmenter.css`, `PipelineViewer.css` e `ControlPanel.css` — por isso a nova
tela já nasce com a mesma cara do restante do app. Só foi criado
`ImageEnhancer.css` com as poucas classes exclusivas da tela nova (grade de
comparação Antes/Depois, banner de "salvo com sucesso" etc.), usando as
mesmas variáveis de design (`--accent-color`, `--radius`, `--shadow`, etc.)
já definidas em `globals.css`.
