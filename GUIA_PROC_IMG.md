# Guia do Pattern Checker

## Visão geral

Este projeto implementa um sistema de segmentação e comparação visual de conteúdo textual em imagens. Ele foi pensado para avaliar se duas imagens possuem o mesmo conteúdo, com um limiar de semelhança para sinalizar plágio ou aceitar a imagem como diferente.

A solução inclui:

- processamento de imagem em Python/OpenCV;
- API REST em FastAPI;
- interface em React com layout moderno e dinâmico;
- análise comparativa entre duas imagens de texto;
- reconstrução visual da leitura com recortes reais de cada letra;
- suporte a deploy em ambiente de produção.

## Arquitetura

### Backend

A lógica principal está em:

- `backend/src/core/segmenters/improved_segmenter.py`
- `backend/src/api/handlers/letter_segmenter_handler.py`
- `backend/src/api/routes/index.py`

O fluxo executado é:

1. decodificação da imagem em base64;
2. pré-processamento com binarização, contraste e ruído;
3. detecção de componentes conectados;
4. filtragem de regiões que não são letras;
5. agrupamento por linha e por palavra;
6. ordenação da leitura;
7. geração dos recortes das letras;
8. comparação com a segunda imagem usando similaridade de sequência.

### Frontend

Os pontos principais do frontend estão em:

- `frontend/src/components/Segmenter/Segmenter.tsx`
- `frontend/src/components/LetterGrid/LetterGrid.tsx`
- `frontend/src/components/ControlPanel/ControlPanel.tsx`
- `frontend/src/services/api.ts`

A interface oferece:

- painel esquerdo com configurações;
- dois uploaders para imagem original e imagem de comparação;
- botão para comparar conteúdo;
- painel de similaridade com status de plágio ou aceitação;
- área de texto reconstruído mostrando cada letra recortada em ordem de leitura.

## Ajustes recentes

### Correção da contagem de letras

Foi ajustado o filtro de componentes para reduzir ruído e fragmentos que não são letras. O problema principal era a presença de regiões esparsas e pequenas, que estavam sendo aceitas como componentes válidos, inflando artificialmente a contagem.

Principais correções:

- aumento do critério mínimo de área útil;
- validação por densidade do componente;
- rejeição de formações muito esparsas ou de baixa cobertura interna;
- preservação das letras reais sem exagerar no filtro.

### Suporte a texto claro em fundo preto

O pré-processamento também foi corrigido para imagens com letras claras sobre fundo preto. Antes, a binarização usava sempre uma máscara invertida, fazendo com que o fundo escuro fosse interpretado como primeiro plano e as letras fossem descartadas durante a detecção.

Agora o sistema:

- analisa a luminância das bordas da imagem para identificar o fundo predominante;
- seleciona automaticamente a polaridade correta da binarização;
- preserva letras claras em fundos escuros e letras escuras em fundos claros;
- aplica a mesma filtragem de ruído e validação nos dois tipos de imagem.

Foi incluído um teste de regressão em `backend/tests/test_segmenter.py` para garantir a detecção de texto claro em fundo preto.

### Responsividade para telas menores

A interface foi ajustada para dispositivos menores com:

- empilhamento das colunas em telas estreitas;
- controle de largura do painel lateral;
- botões com largura total em mobile;
- layout dos cards de comparação e métricas em modo coluna em telas pequenas.

## Regras de comparação

A lógica implementada usa um cálculo aproximado de similaridade com base na sequência detectada e na quantidade de letras que cada imagem contém.

### Limiares

- `>= 0.90` → plágio detectado
- `< 0.70` → imagem aceita
- `>= 0.70` e `< 0.90` → semelhança parcial

Essa regra segue o comportamento solicitado: verificar se as imagens têm o mesmo conteúdo em 90% ou mais, se são muito diferentes ou se se diferenciam pela metade.

## Texto reconstruído em ordem de leitura

A área de exibição foi ajustada para mostrar cada letra recortada de fato, em sequência, em vez de placeholders como `L1`, `L2`, `L3`.

Cada cartão da linha de leitura exibe:

- a letra recortada em imagem;
- o número do recorte;
- a organização visual em ordem de leitura.

## Exportação

Ao clicar em baixar todas, o sistema gera um ZIP com:

- `transcricao.txt` com a sequência organizada;
- todos os recortes em `letras/`.

## Testes e verificação

O projeto possui testes automatizados em:

- `backend/tests/test_segmenter.py`

Os cenários cobertos incluem:

- detecção de letras;
- detecção de texto claro em fundo preto;
- ordenação por palavras;
- robustez a ruído;
- leitura em ordem;
- comparação de imagens com conteúdo idêntico.

## Observações de qualidade

### Quando a solução funciona melhor

- imagens com contraste bom;
- texto legível e nítido;
- sem ruído excessivo;
- fontes bem definidas;
- linhas e palavras separadas com clareza.

### Quando exige cuidado

- imagens muito borradas;
- texto sobre fundo complexo;
- contraste muito baixo;
- artefatos visuais e linhas decorativas;
- letras muito pequenas ou distorcidas.

## Como rodar em desenvolvimento

```bash
# instalar dependências
make install

# backend
# ainda dentro de backend/
rm -rf venv

# volte pra raiz onde está o .venv bom
cd ..

# confirme que está ativado (deve mostrar (.venv))
source .venv/Scripts/activate

# instale as dependências do backend nesse venv
cd backend
pip install -r requirements.txt

# rode o servidor como módulo
python -m src.server


# frontend
cd frontend
npm run dev
```

## Deploy em produção com Vercel + Render

A arquitetura mais simples e estável para este projeto é:

- Frontend em Vercel
- Backend em Render
- Comunicação segura via HTTPS

O projeto já está preparado para esse modelo porque o frontend usa a variável `VITE_API_URL` e o backend lê `ALLOWED_ORIGINS` a partir de variáveis de ambiente.

### 1. Preparar o repositório no GitHub

1. Crie um repositório no GitHub.
2. Faça o push do projeto para a branch principal.
3. Confirme que o `.gitignore` já está ignorando `.venv`, `node_modules`, `dist`, `.env` e arquivos temporários.

```bash
git init
git add .
git commit -m "chore: inicializa projeto"
git branch -M main
git remote add origin https://github.com/seu-usuario/processamento-de-imagens.git
git push -u origin main
```

### 2. Ajuste necessário no backend para o Render

No ambiente do Render, o OpenCV costuma falhar se usar `opencv-python` em container headless. Para evitar erro de biblioteca nativa, configure a dependência como `opencv-python-headless` no arquivo `backend/requirements.txt`:

```txt
opencv-python-headless==4.10.0.84
```

Isso preserva o módulo `cv2` e evita problemas com `libGL.so.1` em servidores sem interface gráfica.

### 3. Deploy do backend no Render

1. Acesse https://render.com
2. Clique em "New +" → "Web Service"
3. Conecte o GitHub e selecione o repositório
4. Configure o serviço assim:
   - Name: `processamento-de-imagens-api`
   - Root Directory: `backend`
   - Runtime: Python
   - Build Command:

```bash
pip install --upgrade pip && pip install -r requirements.txt
```

   - Start Command:

```bash
python -m uvicorn src.server:app --host 0.0.0.0 --port $PORT
```

5. Na seção de variáveis de ambiente, adicione:

```env
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=10000
ALLOWED_ORIGINS=https://seu-app.vercel.app
```

> A variável `PORT` será injetada pelo Render automaticamente, mas pode ser usada em ambiente local como fallback. No Render, o comando acima usa `$PORT`.

6. Salve e aguarde o deploy.
7. Depois de concluído, teste a rota de health check:

```bash
https://seu-backend.onrender.com/health
```

Resposta esperada:

```json
{"status":"ok","service":"letter-segmenter"}
```

### 4. Deploy do frontend na Vercel

1. Acesse https://vercel.com
2. Clique em "Add New Project"
3. Importe o mesmo repositório do GitHub
4. Configure o projeto com:
   - Root Directory: `frontend`
   - Framework Preset: Vite
   - Build Command: `npm install && npm run build`
   - Output Directory: `dist`
5. Adicione a variável de ambiente:

```env
VITE_API_URL=https://seu-backend.onrender.com/api
```

6. Clique em "Deploy".
7. A Vercel vai gerar uma URL pública, por exemplo:

```bash
https://processamento-de-imagens.vercel.app
```

### 5. Liberar o CORS no backend

No Render, atualize a variável `ALLOWED_ORIGINS` para incluir a URL do frontend hospedado na Vercel.

Exemplo:

```env
ALLOWED_ORIGINS=https://processamento-de-imagens.vercel.app
```

Se quiser liberar também preview URLs da Vercel, use:

```env
ALLOWED_ORIGINS=https://processamento-de-imagens.vercel.app,https://processamento-de-imagens-git-main-seuusuario.vercel.app
```

### 6. Validar a integração completa

Depois de publicar os dois serviços, teste:

```bash
curl https://seu-backend.onrender.com/health
```

Em seguida, abra a URL do frontend no navegador e faça um upload de imagem. Os passos esperados são:

1. Frontend envia a imagem para `/api/segment`
2. Backend processa e responde com os resultados
3. UI renderiza a comparação e a sequência detectada
4. Sem erros de CORS no console do navegador

### 7. Checklist final de produção

Antes de liberar para uso real, confirme:

- backend respondendo no `/health`
- frontend carregando corretamente na Vercel
- `VITE_API_URL` apontando para o backend do Render
- `ALLOWED_ORIGINS` incluindo a URL da Vercel
- upload e processamento de imagens funcionando
- logs do Render sem erro de OpenCV ou biblioteca nativa

### 8. Fluxo do deploy em resumo

```text
GitHub → Render (backend) → HTTPS API
GitHub → Vercel (frontend) → HTTPS App
Frontend chama Backend via VITE_API_URL
Backend aceita requisições via ALLOWED_ORIGINS
```

### 9. Observações importantes

- O Render usa `PORT` automaticamente; não fixe a porta manualmente no start command.
- O Vercel faz deploy contínuo a cada `git push` na branch principal.
- O Render também faz redeploy automático ao detectar alterações.
- Em plano gratuito, o backend pode entrar em cold start; isso pode aumentar a primeira requisição em alguns segundos.

## Deploy em ambiente tradicional (opcional)

Se você preferir não usar Vercel + Render, a alternativa seria publicar o backend em um VPS ou máquina Linux e o frontend em Nginx ou outro host estático. Esse modelo também funciona, mas o fluxo recomendado para este projeto continua sendo Vercel + Render.

### Estrutura final recomendada

```text
processamento-de-imagens/
├── backend/
├── frontend/
├── .gitignore
├── README.md
├── GUIA.md
└── Makefile
```

## Conclusão

O passo a passo mais recomendado para este projeto é subir o frontend na Vercel e o backend no Render, usando variáveis de ambiente para conectar os serviços. Isso reduz a complexidade de infraestrutura, oferece HTTPS automático e facilita deploy contínuo por GitHub.



## Comandos uteis do Git para resolver esse erro: remote origin already exists.

git remote remove origin
git remote add origin https://github.com/han19githtbr/process_pics_app.git
git remote -v

## Enviar para o GitHub

git branch -M master
git push -u origin master

## Roteiro real de deploy (Windows + PowerShell) — passo a passo executado

Esta seção documenta, na ordem exata, o processo que foi seguido para colocar este projeto no ar, usando PowerShell no Windows, Render para o backend e Vercel para o frontend.

### 1. Ativar o ambiente virtual (.venv) no PowerShell

Na raiz do projeto (`processamento-de-imagens`), com PowerShell aberto **como Administrador**:

```powershell
.\.venv\Scripts\Activate.ps1
```

O que esse comando faz:

- `.venv` é a pasta que contém uma cópia isolada do Python só para este projeto, com suas próprias bibliotecas (FastAPI, OpenCV, etc.), separada do Python global da máquina.
- `Scripts\Activate.ps1` é o script de ativação específico para PowerShell (no Git Bash o equivalente é `source .venv/Scripts/activate`).
- Ao rodar, ele: (1) ajusta o `PATH` da sessão atual para priorizar os executáveis de dentro de `.venv`; (2) muda o prompt para mostrar `(.venv)` no início, confirmando que está ativo; (3) faz com que `pip install` instale pacotes só dentro dessa pasta, sem afetar o resto do sistema.
- O `.\` no início é exigido pelo PowerShell para rodar scripts do diretório atual.
- A ativação vale só para aquela sessão do terminal — se fechar e abrir de novo, é preciso repetir o comando.

Se aparecer erro de "execution policy" ao ativar, rode antes:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Confirme que o prompt passou a mostrar `(.venv)` no início da linha.

### 2. Instalar as dependências do backend

```powershell
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

**Erro comum no Windows:** `WinError 5: Acesso negado` ao instalar `opencv-python-headless`, geralmente porque o arquivo `cv2.pyd` está em uso por outro processo (servidor rodando, VS Code com terminal Python ativo, antivírus escaneando) ou por falta de permissão.

Soluções, em ordem:

1. Feche qualquer terminal com o backend rodando, feche o VS Code se tiver terminal Python ativo nesse venv.
2. Pause o antivírus temporariamente ou adicione a pasta do projeto às exceções.
3. Rode o PowerShell **como Administrador** e repita o `pip install`.
4. Se persistir, apague manualmente a pasta `backend/.venv/Lib/site-packages/cv2` e reinstale.
5. Último recurso: apague a pasta `.venv` inteira e recrie com `python -m venv .venv`.

### 3. Testar o backend localmente

Ainda dentro de `backend`, com o `.venv` ativado:

```powershell
python -m src.server
```

Isso sobe o servidor Uvicorn em `http://0.0.0.0:8000`. Sem fechar esse terminal, abra outro (ou o navegador) e teste:

```powershell
curl http://localhost:8000/health
```

Resposta esperada:

```json
{"status":"ok","service":"letter-segmenter"}
```

Esse teste confirma que a instalação das dependências funcionou de verdade e que o servidor sobe sem erros, antes de ir para produção.

### 4. Commitar e enviar mudanças para o GitHub

Verificar o estado do repositório antes de subir:

```powershell
git status
git remote -v
```

Se houver arquivos modificados, revisar as mudanças antes de commitar:

```powershell
git diff caminho/do/arquivo.py
```

(no pager que abre, aperte `q` para sair e voltar ao prompt)

Depois, adicionar, commitar e enviar:

```powershell
git add .
git commit -m "chore: melhora robustez das configs de ambiente para deploy"
git push origin master
```

### 5. Deploy do backend no Render

Em [render.com](https://render.com), New + → Web Service → conectar o repositório GitHub. Preencher:

| Campo | Valor |
|---|---|
| Root Directory | `backend` |
| Language | Python 3 |
| Branch | `master` |
| Build Command | `pip install --upgrade pip && pip install -r requirements.txt` |
| Start Command | `python -m uvicorn src.server:app --host 0.0.0.0 --port $PORT` |
| Plano | Free (para começar) |

Variáveis de ambiente adicionadas:

```env
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=10000
ALLOWED_ORIGINS=https://seu-app.vercel.app   # valor temporário, atualizado depois
```

Clicar em **Deploy web service** e aguardar o build. Ao final, o Render fornece uma URL pública, por exemplo:

```
https://process-pics-app.onrender.com
```

Testar o health check da URL pública:

```powershell
curl https://process-pics-app.onrender.com/health
```

Resposta esperada: `200 OK` com `{"status":"ok","service":"letter-segmenter"}`.

### 6. Deploy do frontend na Vercel

Em [vercel.com](https://vercel.com), Add New → Project → importar o mesmo repositório GitHub. Preencher:

| Campo | Valor |
|---|---|
| Root Directory | `frontend` |
| Application Preset | Vite (detectado automaticamente) |
| Build Command | `npm install && npm run build` (padrão) |
| Output Directory | `dist` (padrão) |

Expandir **Environment Variables** e adicionar:

```env
VITE_API_URL=https://process-pics-app.onrender.com/api
```

Clicar em **Deploy**. Ao final, status **Ready** e domínio público, por exemplo:

```
https://process-pics-app.vercel.app
```

### 7. Atualizar o CORS no backend com a URL real da Vercel

Voltar ao Render → serviço do backend → **Environment** → editar a variável `ALLOWED_ORIGINS`, trocando o valor temporário pela URL real gerada pela Vercel:

```env
ALLOWED_ORIGINS=https://process-pics-app.vercel.app
```

Salvar. O Render faz redeploy automático para aplicar a nova variável — aguardar até o status voltar a **Live**.

### 8. Validar a integração completa

Abrir a URL do frontend no navegador, fazer upload de uma imagem e testar a comparação. Abrir o Console do navegador (F12) e confirmar que não há erros de CORS.

### Resumo do fluxo

```text
.venv ativado → dependências instaladas → backend testado local (/health)
        ↓
git add / commit / push → GitHub atualizado
        ↓
Render (backend) → deploy → URL pública testada (/health)
        ↓
Vercel (frontend) → deploy com VITE_API_URL apontando pro backend
        ↓
Render: ALLOWED_ORIGINS atualizado com a URL real da Vercel
        ↓
Teste end-to-end no navegador, sem erros de CORS
```
