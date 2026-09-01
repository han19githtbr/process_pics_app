# Pattern Checker

Aplicação de segmentação e comparação de conteúdo visual em imagens de texto, com foco em detectar semelhança entre duas imagens e sinalizar plágio quando o conteúdo for muito parecido.

## Visão geral

Este projeto combina Python/OpenCV, FastAPI e React para:

- segmentar letras de uma imagem de texto;
- reconstruir a sequência em ordem de leitura;
- exibir cada letra recortada visualmente;
- comparar duas imagens para medir similaridade de conteúdo;
- classificar o resultado com thresholds de plágio e aceitação.

## Funcionalidades implementadas

- Segmentação robusta de letras por componentes conectados
- Organização correta por linha e por palavra
- Exibição dos recortes individuais em uma grade visual
- Texto reconstruído mostrando os recortes reais da imagem, sem placeholders de L1/L2/L3
- Comparação entre duas imagens com cálculo percentual de similaridade
- Classificação automática:
  - > 90%: plágio detectado
  - < 70%: imagem aceita
  - entre 70% e 90%: semelhança parcial
- Exportação dos recortes em ZIP
- Interface moderna com painel de configuração e análise comparativa

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
python src/server.py

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

