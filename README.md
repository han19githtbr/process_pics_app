# Pattern Checker

Aplicação de segmentação e comparação de conteúdo visual em imagens de texto, com foco em detectar semelhança entre duas imagens e sinalizar plágio quando o conteúdo for muito parecido.

## Visão geral

Este projeto é baseado no trabalho acadêmico **"Processamento de Imagens: Processamento de Imagens de Textos"** (UFRRJ — TM438, Prof. Bruno Dembogurski, autores Handy Claude Milliance & Deived William da Silva Azevedo) e combina Python/OpenCV, FastAPI e React para:

- executar fielmente o pipeline de 7 etapas conceituais do trabalho acadêmico;
- converter pixels RGB para tons de cinza com a fórmula de luminância $Y \leftarrow 0.299 \cdot R + 0.587 \cdot G + 0.114 \cdot B$;
- aplicar suavização por Filtro Bilateral ($d=10, \sigma=75$) preservador de bordas;
- binarizar via Método de Otsu com inversão `bitwise_not`;
- detectar bordas via Algoritmo de Canny com limiares 70 e 150;
- identificar contornos com compressão `cv2.CHAIN_APPROX_SIMPLE` e calcular `boundingRect`;
- recortar individualmente as letras e reconstruir a sequência em ordem de leitura;
- **desmembrar letras agrupadas** por análise de vales no perfil de projeção vertical de tinta;
- **filtrar elementos não-letras** (linhas horizontais, molduras, blocos sólidos e poeiras de digitalização);
- expor visualmente no Frontend todas as 7 etapas intermediárias geradas pelo OpenCV;
- fornecer um painel de **Transparência e Honestidade Técnica** explicando imperfeições e causas de ruído;
- comparar duas imagens para medir similaridade de conteúdo e detectar plágio;
- manter histórico com persistência em MongoDB Atlas e fallback local em memória;
- exportar os recortes em arquivo ZIP.

## Pipeline do Trabalho Acadêmico (PDF UFRRJ)

| Passo | Etapa | Técnica OpenCV / Conceito | Propósito |
| :--- | :--- | :--- | :--- |
| **1** | **Imagem Load** | `cv2.imread` (matriz NumPy $H \times W \times 3$) | Carregamento da imagem em array com profundidade de cor de 24 bits. |
| **2** | **Tons de Cinza** | $Y \leftarrow 0.299R + 0.587G + 0.114B$ (`cv2.cvtColor`) | Representa a intensidade luminosa de cada pixel em um único valor [0..255]. |
| **3** | **Filtro Bilateral** | `cv2.bilateralFilter(gray, 10, 75, 75)` | Suavização que remove ruído de alta frequência preservando a nitidez das arestas. |
| **4** | **Binarização** | Método de Otsu + `cv2.bitwise_not` | Limiar estatístico ótimo $T$ para isolar o texto do fundo. |
| **5** | **Detecção de Bordas** | `cv2.Canny(bin, 70, 150)` | Operador direcional com derivadas de Sobel e histerese. |
| **6** | **Contornos** | `cv2.findContours(RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)` | Rastreamento de fronteiras com compressão de pontos redundantes. |
| **7** | **Recorte & Leitura** | `x,y,w,h = boundingRect(c); curt = img[y:y+h, x:x+w]` | Extração matricial individual e ordenação por linha/palavra. |

## Stack

### Backend
- Python 3.11+
- OpenCV
- FastAPI
- NumPy
- Pytest

### Frontend
- React 18
- TypeScript
- Vite
- Axios
- JSZip

## Como executar

### Requisitos
- Python 3.11+
- Node.js 18+
- npm

### Instalação

```bash
# raiz do projeto
make install
```

Ou manualmente:

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

### Execução

```bash
# backend
cd backend
python -m src.server

# frontend em outra sessão/terminal
cd frontend
npm run dev
```

A API fica em `http://localhost:8000/api` e o frontend em `http://localhost:5173`.

## Endpoints principais

- `POST /api/segment` — segmenta uma imagem e retorna letras, debug e transcript
- `POST /api/compare` — compara duas imagens e retorna grau de similaridade e status
- `GET /api/health` — saúde da API

## Testes

```bash
cd backend
python -m pytest tests/test_segmenter.py -q
```

## Observações importantes

- O texto reconstruído da área de leitura mostra os recortes reais das letras para preservar a fidelidade visual da segmentação.
- A comparação é baseada na similaridade entre transcrições e no número de letras detectadas em cada imagem.
- A classificação é orientativa e depende da qualidade da imagem, do contraste e da segmentação inicial.

## Estrutura

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

## Comandos para instalar o Antigravity CLI 

rm -rf "$LOCALAPPDATA/agy" ~/.config/agy ~/.antigravity

Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://antigravity.google/cli/install.ps1'))
