# Guia do projeto Pattern Checker

## 1. Visão geral

Este projeto implementa um sistema de segmentação e comparação visual de conteúdo textual em imagens. A aplicação foi desenvolvida para:

- segmentar letras de imagens de texto;
- reconstruir a sequência em ordem de leitura;
- exibir cada letra recortada visualmente;
- comparar duas imagens para medir similaridade de conteúdo e sinalizar possível plágio;
- persistir o histórico de imagens processadas (em MongoDB Atlas, com fallback em memória quando o Mongo não está configurado);
- buscar itens do histórico pelo nome do arquivo ou pela transcrição, com destaque do termo encontrado;
- baixar as letras recortadas e a transcrição em um `.zip`;
- apresentar uma interface de dashboard premium em dark/light mode para revisão e análise profissional.

A solução combina Python/OpenCV, FastAPI e React para processar texto em imagens, identificar ruídos e manter a leitura em ordem correta.

## 2. Funcionalidades implementadas

- Segmentação robusta de letras por componentes conectados
- Organização correta por linha e por palavra
- Rebuild visual da leitura com recortes reais das letras
- Comparação entre duas imagens com cálculo percentual de similaridade
- Classificação automática de resultado:
  - similaridade ≥ 90%: `plagio_detectado`
  - similaridade < 70%: `imagem_aceita`
  - entre 70% e 90%: `semelhanca_parcial`
- Histórico de imagens processadas, com salvamento automático (quando o MongoDB está conectado) e salvamento manual via botão "Salvar" (funciona mesmo sem MongoDB, usando fallback em memória)
- Busca no histórico por nome do arquivo ou transcrição (`GET /api/history/search`), com debounce de 350ms e destaque (`<mark>`) do trecho encontrado no nome do arquivo
- Consulta do histórico no frontend com visualização da imagem e das letras recortadas
- Download de todas as letras recortadas + transcrição em um arquivo `.zip` (via JSZip, gerado no navegador)
- Área de recortes com tamanho fixo e scroll vertical
- Persistência opcional em MongoDB Atlas para produção, com fallback local automático quando `MONGODB_URI` não é definida

## 3. Visual e experiência do produto

A interface passou por uma reformulação de identidade visual para se alinhar com o que a ferramenta realmente faz: uma análise técnica e objetiva de segmentação e comparação de imagens. A paleta anterior (rosa, ciano e amarelo neon sobre fundo roxo) foi substituída por um sistema mais sóbrio e consistente:

- fundo em grafite neutro (dark mode) e cinza muito claro (light mode), sem gradientes decorativos concorrendo com o conteúdo;
- um único acento de marca (índigo, `#5b7cfa`) usado com moderação em botões, links e destaques — em vez de múltiplas cores vibrantes disputando atenção;
- cores reservadas para significado, não decoração: verde para "imagem aceita", âmbar para "similaridade parcial" e vermelho para "plágio detectado", usadas apenas nesses contextos de status;
- painéis com bordas de 1px e sombras discretas no lugar do efeito "vidro" (glassmorphism) pesado, o que melhora a legibilidade e a hierarquia entre os blocos de upload, comparação e histórico;
- tipografia mantida em Space Grotesk (títulos) e DM Sans (texto), com pesos e tamanhos ajustados para reduzir o exagero visual dos títulos grandes;
- ícones existentes (emoji) padronizados em selos circulares com o tom do acento de marca, criando um sistema visual coeso entre painel de configurações, upload e cabeçalhos;
- cabeçalho alinhado à esquerda, mais compacto e com contraste mais equilibrado entre título, subtítulo e o botão de alternância de tema;
- correção de duas inconsistências técnicas: uma regra de CSS duplicada em `ControlPanel.css` que conflitava com os estilos de `ImageUploader.css`, e a variável `--card-background`, usada em alguns componentes mas nunca definida — ambas causavam comportamento visual imprevisível dependendo da ordem de carregamento dos estilos;
- contraste de texto revisado em botões, badges e mensagens de erro para atender melhor aos critérios de legibilidade (AA) em ambos os temas;
- foco de teclado visível (`:focus-visible`) e respeito a `prefers-reduced-motion` adicionados como base de acessibilidade;
- responsividade mantida e revisada para desktop, tablet e celular, sem quebrar o layout em nenhuma largura testada;
- campo de busca do histórico com ícone de lupa, spinner enquanto a busca roda, botão de limpar (✕) e mensagem de status ("N resultados encontrados" / "Nenhuma imagem encontrada").

Esse refinamento foi aplicado ao layout principal, ao painel de configurações, aos cards de upload, ao painel de histórico, ao bloco de comparação e à grade de letras. Nenhuma estrutura de componente (`.tsx`) foi alterada — apenas os arquivos `.css`.

## 4. Stack

### Backend
- Python 3.10+
- OpenCV (`opencv-python-headless`)
- FastAPI
- NumPy
- Pytest / pytest-cov
- PyMongo
- python-dotenv

### Frontend
- React 18
- TypeScript
- Vite
- Axios
- JSZip

## 5. Requisitos

- Python 3.10+
- Node.js 18+
- npm
- MongoDB Atlas account (opcional — a aplicação funciona sem ele, ver seção 11)
- Git

## 6. Preparar o backend

Na raiz do projeto:

```powershell
cd backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

No Linux/macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 7. Configurar as variáveis de ambiente

Crie um arquivo `.env` dentro da pasta `backend` (existe um `.env.example` com o mesmo conteúdo como referência):

```env
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
MONGODB_URI=mongodb+srv://<usuario>:<senha>@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=pattern_checker
MONGODB_COLLECTION_NAME=processed_images
CACHE_ENABLED=false
MAX_IMAGE_SIZE=1800
```

Para produção, use uma coleção separada:

```env
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=https://seu-frontend.vercel.app
MONGODB_URI=mongodb+srv://<usuario>:<senha>@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=pattern_checker
MONGODB_COLLECTION_NAME=processed_images_prod
```

> `MONGODB_COLLECTION_NAME` também é resolvido automaticamente com base em `ENVIRONMENT`: se não for definido, o backend usa `processed_images_prod` quando `ENVIRONMENT=production` e `processed_images` em qualquer outro caso.

### Como obter a string do MongoDB Atlas

1. Acesse https://www.mongodb.com/cloud/atlas
2. Crie o cluster
3. Vá em Database Access e crie um usuário com senha
4. Vá em Network Access e adicione seu IP ou `0.0.0.0/0`
5. Vá em Database > Connect > Connect your application
6. Copie a string de conexão e cole em `MONGODB_URI`

## 8. Rodar o backend localmente

```powershell
cd backend
. .venv\Scripts\Activate.ps1
python -m src.server
```

Teste o health check:

```powershell
curl http://localhost:8000/health
```

Resposta esperada:

```json
{"status": "ok", "service": "letter-segmenter"}
```

## 9. Preparar o frontend

No diretório do frontend:

```powershell
cd frontend
npm install
npm run dev
```

A aplicação normalmente fica em:

```text
http://localhost:5173
```

## 10. Configurando a URL da API no frontend

No Vite, a variável pode ser configurada em um arquivo `.env.local` do frontend (existe `.env.example` como referência):

```env
VITE_API_URL=http://localhost:8000/api
```

Para produção no Render:

```env
VITE_API_URL=https://seu-backend.onrender.com/api
```

## 11. Persistência do histórico

O histórico de imagens processadas pode ser persistido de duas formas, dependendo da configuração:

- **Com `MONGODB_URI` definida e conexão bem-sucedida:** o backend salva no MongoDB Atlas. Essa escolha faz sentido pelo volume de imagens e textos longos, porque o MongoDB aceita documentos flexíveis, armazena metadados, imagens em base64 e recortes em arrays sem exigir um esquema rígido.
- **Sem `MONGODB_URI` (ou com falha de conexão):** o backend usa um histórico **em memória**, mantido enquanto o processo do servidor estiver rodando. Ele é perdido a cada reinício/deploy, mas permite testar todo o fluxo (segmentar, salvar, listar, buscar, abrir item) sem depender de um banco externo.

Quando houver processamento bem-sucedido em `POST /api/segment`, o backend salva **automaticamente** no histórico apenas se o MongoDB estiver conectado (`is_enabled`). O salvamento manual pelo botão "Salvar" no histórico (`POST /api/history/save`) funciona em ambos os casos — Mongo conectado ou fallback em memória.

O que é salvo em cada registro:

- imagem original em base64;
- nome do arquivo;
- transcrição em ordem de leitura;
- recortes das letras;
- métricas e metadados;
- data e hora do processamento (`createdAt`/`updatedAt`).

A coleção padrão em desenvolvimento é:

```text
processed_images
```

Em produção, o padrão recomendado/automático é:

```text
processed_images_prod
```

Isso evita misturar dados locais com registros de produção.

## 12. Histórico e busca no frontend

A interface possui um painel de histórico de imagens processadas com:

- miniatura da imagem;
- texto transcrito;
- nome do arquivo, com o termo pesquisado destacado quando há busca ativa;
- item clicável para abrir a imagem do histórico e visualizar as letras recortadas;
- scroll vertical para navegar entre todas as letras recortadas;
- campo de busca (`Buscar por nome do arquivo salvo...`) que filtra pelo nome do arquivo **ou** pela transcrição no backend, com debounce de 350ms para evitar uma chamada a cada tecla digitada;
- botão "Atualizar", que recarrega a lista completa ou repete a busca atual;
- botão de limpar busca (✕) que volta a listar todo o histórico.

A área de recortes usa tamanho fixo e rolagem vertical para mostrar todas as letras quando houver muitas.

## 13. Ordem correta das letras

A lógica de recorte foi ajustada para remover ruído e preservar a ordem real do texto.

Exemplo: `SAMPLE HERE`

Resultado esperado:

```text
S, A, M, P, L, E, H, E, R, E
```

Além disso, o backend:

- filtra componentes que não são letras;
- rejeita regiões muito esparsas ou de baixa cobertura interna;
- preserva a sequência por linha e palavra;
- organiza os recortes seguindo a leitura natural do texto.

## 14. Comparação e detecção de similaridade

`POST /api/compare` segmenta as duas imagens recebidas, monta a transcrição de cada uma e calcula a similaridade com `difflib.SequenceMatcher` sobre os textos reconstruídos. Se ambas as imagens tiverem letras detectadas, a similaridade final é o maior valor entre essa razão textual e a razão entre as quantidades de letras (a menor contagem dividida pela maior).

Classificação aplicada sobre a similaridade (0 a 1):

| Similaridade | Status              | Significado                                         |
|---|---|---|
| ≥ 0.90        | `plagio_detectado`  | Conteúdo altamente semelhante ao original           |
| 0.70 – 0.90   | `semelhanca_parcial`| Semelhança parcial, exige revisão manual            |
| < 0.70        | `imagem_aceita`     | Conteúdo muito diferente, pode ser aceito           |

A resposta inclui a contagem de letras de cada imagem, os thresholds usados e as transcrições de origem e comparação.

## 15. Principais endpoints da API

Todas as rotas abaixo (exceto `/health` na raiz) ficam sob o prefixo `/api`.

| Método | Rota                    | Descrição                                                              |
|---|---|---|
| POST   | `/api/segment`           | Segmenta uma imagem e retorna letras, transcript e dados do processamento |
| POST   | `/api/compare`           | Compara duas imagens e retorna grau de similaridade e status            |
| GET    | `/api/history`           | Lista os últimos 20 itens do histórico                                  |
| GET    | `/api/history/search?q=` | Busca itens do histórico por nome do arquivo ou transcrição             |
| POST   | `/api/history/save`      | Salva manualmente uma imagem processada no histórico                    |
| GET    | `/api/history/{item_id}` | Retorna um item específico do histórico por ID                          |
| OPTIONS| `/api/segment`, `/api/compare`, `/api/history` | Respostas de CORS (preflight)                          |
| GET    | `/api/health`            | Health check da API                                                     |
| GET    | `/health`                | Health check equivalente, fora do prefixo `/api`                        |
| GET    | `/`                      | Rota raiz com nome, versão e status do serviço                          |

> Importante: `/api/history/search` precisa estar registrada **antes** de `/api/history/{item_id}` no router. Como o FastAPI casa rotas na ordem de registro, se a rota dinâmica vier primeiro, uma chamada para `/api/history/search` é interpretada como `item_id="search"` e falha com erro de `ObjectId` inválido. Essa ordem já está correta em `backend/src/api/routes/index.py`.

Em caso de erro não tratado em qualquer rota, o middleware `error_handler.py` captura a exceção, imprime o traceback completo no log do servidor e devolve `500` com o corpo `{"error": "Erro interno do servidor", "message": "<mensagem da exceção>"}` — útil para depurar diretamente pela aba Response do DevTools ou pelos logs do Render.

## 16. Arquitetura e fluxo principal

### Backend

```text
backend/src/
  server.py                          # cria o FastAPI app, CORS e inclui o router com prefixo /api
  config/settings.py                 # lê variáveis de ambiente (.env)
  api/routes/index.py                # define todas as rotas
  api/handlers/letter_segmenter_handler.py  # orquestra segmentação, comparação e histórico
  api/middleware/error_handler.py    # captura exceções não tratadas e devolve JSON 500
  core/factory/segmenter_factory.py  # cria o segmentador padrão
  core/segmenters/improved_segmenter.py  # segmentação, agrupamento por linha/palavra e comparação
  core/processors/opencv_processor.py    # pré-processamento de imagem (binarização, contraste, ruído)
  core/validators/letter_validator.py    # filtra componentes que não são letras
  core/utils/image_utils.py          # decodificação de imagens base64 (data URL)
  core/utils/geometry_utils.py       # cálculos geométricos auxiliares (posições, agrupamento)
  core/models/                       # modelos de dados (LetterBox, SegmentResult, ProcessingOptions)
  services/mongodb_service.py        # persistência em MongoDB Atlas com fallback em memória
```

Fluxo executado em `POST /api/segment`:

1. decodificação da imagem em base64;
2. pré-processamento com binarização, contraste e ruído;
3. detecção de componentes conectados;
4. filtragem de regiões que não são letras;
5. agrupamento por linha e por palavra;
6. ordenação da leitura;
7. geração dos recortes das letras;
8. salvamento automático do registro no MongoDB, quando habilitado;
9. retorno ao frontend para exibição e histórico.

### Frontend

```text
frontend/src/
  components/Segmenter/Segmenter.tsx    # tela principal: upload, comparação, histórico, busca, download
  components/LetterGrid/LetterGrid.tsx  # grade de letras recortadas + botão de download em .zip
  components/ControlPanel/ControlPanel.tsx  # painel de configurações de segmentação
  components/ImageUploader/ImageUploader.tsx # upload/preview da imagem original e de comparação
  components/common/                    # LoadingSpinner e ErrorMessage
  hooks/useSegmenter.ts                 # chama POST /api/segment e mantém estado de loading/erro
  hooks/useImageUpload.ts               # controla upload/preview de uma imagem
  services/api.ts                       # client axios para todos os endpoints da API
```

A interface oferece:

- painel esquerdo com configurações (sensibilidade, padding, tamanho mín./máx. de letra, remoção de ruído, modo de threshold, tamanho máximo da imagem);
- upload de imagem original e de imagem de comparação;
- comparação por imagem de referência, com painel de similaridade e status de plágio/aceitação/revisão manual;
- painel de histórico com busca, atualização e seleção de item salvo;
- área de texto reconstruído com recortes reais em ordem de leitura;
- botão para baixar todas as letras recortadas + transcrição em um `.zip` (gerado no navegador com JSZip, sem chamada ao backend).

## 17. Deploy com Render (backend)

No Render, configure as variáveis de ambiente do serviço backend assim:

```env
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
DEBUG=false
ALLOWED_ORIGINS=https://seu-frontend.vercel.app
MONGODB_URI=mongodb+srv://usuario:senha@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=pattern_checker
MONGODB_COLLECTION_NAME=processed_images_prod
```

### Passo a passo no Render

1. Crie um novo Web Service.
2. Conecte o repositório do projeto.
3. Defina o diretório do backend.
4. Use o comando de build:

```bash
pip install -r requirements.txt
```

5. Use o comando de start:

```bash
python -m src.server
```

6. Adicione as variáveis de ambiente acima.
7. Faça o deploy.

> No plano free do Render, a instância "dorme" após um período de inatividade e a primeira requisição depois disso pode demorar até ~50 segundos ou mais para responder (cold start).

### Confirmando que o deploy certo está no ar

Depois de dar `git push`, confira na aba **Events** do serviço no Render se o deploy mais recente corresponde ao commit esperado (o hash aparece ao lado de "Deploy live for..."). Se o auto-deploy não disparar ou o commit não bater, use **Manual Deploy → Deploy latest commit** para forçar a atualização — código corrigido localmente só tem efeito em produção depois desse passo.

## 18. Deploy no Vercel (frontend)

No Vercel, configure a variável de ambiente do frontend:

```env
VITE_API_URL=https://seu-backend.onrender.com/api
```

### Passo a passo no Vercel

1. Crie o projeto no Vercel.
2. Conecte o repositório frontend.
3. Defina a pasta do projeto como `frontend`.
4. Configure a variável `VITE_API_URL` com a URL pública do backend no Render.
5. Faça o deploy.

## 19. Testes e verificação

O projeto possui testes automatizados em:

- `backend/tests/test_segmenter.py` — segmentação e comparação de imagens
- `backend/tests/test_mongodb_history.py` — comportamento do serviço de MongoDB (nome de coleção, documento de histórico)
- `backend/tests/test_history_save.py` — salvamento e recuperação manual de itens do histórico

Comandos úteis:

```bash
cd backend
pytest tests/ -q
```

Ou rodando arquivos específicos:

```bash
pytest tests/test_segmenter.py tests/test_mongodb_history.py tests/test_history_save.py -q
```

## 20. Estrutura do projeto

```text
backend/
  src/
  tests/
  requirements.txt
  .env.example
frontend/
  src/
  package.json
  .env.example
scripts/
  setup.sh
GUIA.md
GUIA_PROC_IMG.md
README.md
Makefile
```

## 21. Observações importantes

- Se `MONGODB_URI` estiver vazia (ou a conexão falhar), o aplicativo **continua salvando o histórico**, mas apenas em memória — os registros somem a cada reinício/redeploy do backend.
- Existe um arquivo `backend/src/api/middleware/cors.py` com uma implementação alternativa de CORS que **não está em uso**; o CORS ativo é configurado em `server.py` via `fastapi.middleware.cors.CORSMiddleware`. Pode ser removido com segurança se causar confusão.
- Há um `index.py` solto na raiz do projeto (fora de `backend/`) com versões antigas e incompletas das rotas `/segment` e `/health`. Ele não é o ponto de entrada usado em desenvolvimento nem em produção (que é `backend/src/server.py`) — mantenha isso em mente para não editá-lo por engano achando que é o app real.
- Para produção, mantenha a senha em variável de ambiente segura e não comite `.env`.
- Para internet pública, configure IPs ou rede segura no Atlas.
- O arquivo de documentação principal é este `GUIA.md`, que reúne toda a visão do projeto, incluindo deploy, MongoDB e busca no histórico.

## 22. Dicas de uso

- use imagens com contraste bom e texto nítido para melhores resultados;
- prefira imagens sem ruído excessivo;
- mantenha o `ALLOWED_ORIGINS` consistente com a URL do frontend em produção;
- em ambientes de produção, não exponha a string de conexão do Atlas em arquivos versionados;
- ao adicionar novas rotas com parâmetro dinâmico (`/algo/{id}`), registre-as **depois** das rotas estáticas equivalentes (`/algo/especifico`) para evitar que uma capture a outra por engano.

