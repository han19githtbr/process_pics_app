# Guia do projeto Pattern Checker

## 1. Visão geral

Este projeto implementa um sistema de segmentação e comparação visual de conteúdo textual em imagens. A aplicação foi desenvolvida para:

- segmentar letras de imagens de texto;
- reconstruir a sequência em ordem de leitura;
- exibir cada letra recortada visualmente;
- comparar duas imagens para medir similaridade de conteúdo;
- persistir o histórico de imagens processadas no MongoDB Atlas;
- permitir consultar imagens antigas e suas letras recortadas no frontend;
- apresentar uma interface de dashboard premium em dark mode para revisão e análise profissional.

A solução combina Python/OpenCV, FastAPI e React para processar texto em imagens, identificar ruídos e manter a leitura em ordem correta.

## 2. Funcionalidades implementadas

- Segmentação robusta de letras por componentes conectados
- Organização correta por linha e por palavra
- Rebuild visual da leitura com recortes reais das letras
- Comparação entre duas imagens com cálculo percentual de similaridade
- Classificação automática de resultado:
  - acima de 90%: plágio detectado
  - abaixo de 70%: imagem aceita
  - entre 70% e 90%: similaridade parcial
- Histórico de imagens processadas com MongoDB
- Consulta do histórico no frontend com visualização da imagem e das letras recortadas
- Área de recortes com tamanho fixo e scroll vertical
- Persistência opcional em MongoDB Atlas para produção

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
- responsividade mantida e revisada para desktop, tablet e celular, sem quebrar o layout em nenhuma largura testada.

Esse refinamento foi aplicado ao layout principal, ao painel de configurações, aos cards de upload, ao painel de histórico, ao bloco de comparação e à grade de letras. Nenhuma estrutura de componente (`.tsx`) foi alterada — apenas os arquivos `.css`.

## 4. Stack

### Backend
- Python 3.10+
- OpenCV
- FastAPI
- NumPy
- Pytest
- PyMongo

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
- MongoDB Atlas account
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

## 7. Configurar as variáveis de ambiente

Crie um arquivo `.env` dentro da pasta `backend` com o conteúdo abaixo:

```env
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
MONGODB_URI=mongodb+srv://<usuario>:<senha>@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=pattern_checker
MONGODB_COLLECTION_NAME=processed_images
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

No Vite, a variável pode ser configurada em um arquivo `.env.local` do frontend:

```env
VITE_API_URL=http://localhost:8000/api
```

Para produção no Render:

```env
VITE_API_URL=https://seu-backend.onrender.com/api
```

## 11. Persistência no MongoDB Atlas

A aplicação agora pode persistir o histórico de imagens processadas no MongoDB Atlas. Essa escolha faz sentido para o volume de imagens e textos longos porque o MongoDB aceita documentos flexíveis, armazena ampla quantidade de metadados, imagens em base64 e recortes em arrays sem exigir um esquema rígido.

Quando houver processamento bem-sucedido, o backend salva automaticamente:

- imagem original em base64;
- nome do arquivo;
- transcrição em ordem de leitura;
- recortes das letras;
- métricas e metadados;
- data e hora do processamento.

A coleção padrão em desenvolvimento é:

```text
processed_images
```

Em produção, o padrão recomendado é:

```text
processed_images_prod
```

Isso evita misturar dados locais com registros de produção.

## 12. Histórico no frontend

A interface possui um painel de histórico de imagens processadas com:

- miniatura da imagem;
- texto transcrito;
- item clicável para abrir a imagem do histórico;
- visualização das letras recortadas;
- scroll vertical para navegar entre todas as letras recortadas.

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

## 14. Principais endpoints da API

- `POST /api/segment` — segmenta uma imagem e retorna letras, transcript e dados do processamento
- `POST /api/compare` — compara duas imagens e retorna grau de similaridade e status
- `GET /api/history` — lista o histórico salvo em MongoDB
- `GET /api/history/{item_id}` — busca um item do histórico por ID
- `GET /api/health` — health check da API

## 15. Arquitetura e fluxo principal

### Backend

A lógica principal está em:

- `backend/src/core/segmenters/improved_segmenter.py`
- `backend/src/api/handlers/letter_segmenter_handler.py`
- `backend/src/api/routes/index.py`
- `backend/src/services/mongodb_service.py`

Fluxo executado:

1. decodificação da imagem em base64;
2. pré-processamento com binarização, contraste e ruído;
3. detecção de componentes conectados;
4. filtragem de regiões que não são letras;
5. agrupamento por linha e por palavra;
6. ordenação da leitura;
7. geração dos recortes das letras;
8. salvamento do registro no MongoDB (quando habilitado);
9. retorno ao frontend para exibição e histórico.

### Frontend

Os pontos principais do frontend estão em:

- `frontend/src/components/Segmenter/Segmenter.tsx`
- `frontend/src/components/LetterGrid/LetterGrid.tsx`
- `frontend/src/components/ControlPanel/ControlPanel.tsx`
- `frontend/src/services/api.ts`

A interface oferece:

- painel esquerdo com configurações;
- upload de imagem original;
- comparação por imagem de referência;
- painel de similaridade com status de plágio ou aceitação;
- revisão do histórico;
- área de texto reconstruído com recortes reais em ordem de leitura.

## 15. Deploy com Render (backend)

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

## 16. Deploy no Vercel (frontend)

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

## 17. Testes e verificação

O projeto possui testes automatizados em:

- `backend/tests/test_segmenter.py`
- `backend/tests/test_mongodb_history.py`

Comandos úteis:

```bash
cd backend
pytest tests/test_segmenter.py tests/test_mongodb_history.py -q
```

## 18. Estrutura do projeto

```text
backend/
  src/
  tests/
frontend/
  src/
GUIA.md
README.md
Makefile
```

## 19. Observações importantes

- Se `MONGODB_URI` estiver vazia, o aplicativo continua funcionando sem salvar histórico.
- Para produção, mantenha a senha em variável de ambiente segura e não comite `.env`.
- Para internet pública, configure IPs ou rede segura no Atlas.
- O arquivo de documentação principal agora está em `GUIA.md` e reúne toda a visão do projeto, incluindo deploy e MongoDB.

## 20. Dicas de uso

- use imagens com contraste bom e texto nítido para melhores resultados;
- prefira imagens sem ruído excessivo;
- mantenha o `ALLOWED_ORIGINS` consistente com a URL do frontend em produção;
- em ambientes de produção, não exponha a string de conexão do Atlas em arquivos versionados.

