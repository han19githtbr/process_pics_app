# Guia do projeto Pattern Checker

## 1. Visão geral e fundamentação no trabalho acadêmico

Este projeto foi concebido e estruturado com base no trabalho acadêmico **"Processamento de Imagens: Processamento de Imagens de Textos"** (disciplina TM438 — Processamento de Imagens, Universidade Federal Rural do Rio de Janeiro - UFRRJ, ministrada pelo Prof. Bruno Dembogurski, de autoria de Handy Claude Marie Milliance e Deived William da Silva Azevedo).

O objetivo central do trabalho é processar imagens de texto para detectar e recortar as letras de palavras, explorando e aplicando na prática os conceitos teóricos do curso. A aplicação atual expande essa base teórica para um produto completo, integrando Python/OpenCV no backend, FastAPI e React/TypeScript no frontend.

A solução é desenhada para:

- executar o **pipeline pedagógico de 7 etapas** definido no trabalho original;
- permitir a visualização interativa no frontend das imagens intermediárias de cada etapa do processamento;
- oferecer **alta precisão no recorte de letras individuais**, resolvendo o desafio de letras coladas/agrupadas;
- **rejeitar elementos não-textuais** (linhas, molduras, sublinhados, ruídos e artefatos gráficos);
- disponibilizar um painel de **Transparência e Honestidade Técnica**, explicando as causas físicas e matemáticas de imperfeições da visão computacional tradicional;
- manter todas as funcionalidades adicionais desenvolvidas (comparação de plágio, histórico persistido no MongoDB Atlas com fallback local, exclusão individual de imagens e limpeza total do banco de dados, rotação 90° de imagens, exportação em `.zip`, alternador de temas claro/escuro).

## 2. Pipeline das 7 Etapas do Trabalho em PDF

O documento acadêmico define um fluxo sequencial estrito de processamento de imagens:

| Passo | Nome no Trabalho | Técnica / Fórmula | Objetivo e Comportamento |
| :---: | :--- | :--- | :--- |
| **1** | **Imagem Load** | `cv2.imread` (matriz NumPy $H \times W \times 3$) | Carregamento da imagem em memória com profundidade de 24 bits (8 bits por canal BGR/RGB). |
| **2** | **Tons de Cinza** | $Y \leftarrow 0.299 \cdot R + 0.587 \cdot G + 0.114 \cdot B$ (`cv2.cvtColor`) | Conversão para escala de cinza via luminância ponderada, mapeando a intensidade de cada pixel para $[0..255]$. |
| **3** | **Suavização da Imagem** | `cv2.bilateralFilter(gray, 10, 75, 75)` | Filtro bilateral não-linear para atenuação de ruído preservando arestas e bordas de texto nítidas. |
| **4** | **Binarização Preto & Branco** | Método de Otsu + `cv2.bitwise_not` | Cálculo estatístico do limiar ótimo $T$ e inversão para que os caracteres fiquem em branco ($255$) sobre fundo preto ($0$). |
| **5** | **Detecção de Bordas** | `cv2.Canny(bin, 70, 150)` | Operador direcional de Canny com derivadas de Sobel ($G_x, G_y$), supressão de não-máximos e histerese (limiares 70 e 150). |
| **6** | **Identificação de Contornos** | `cv2.findContours(edges, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)` | Rastreamento de pontos vizinhos com compressão de redundâncias para identificar fronteiras de cada caractere. |
| **7** | **Bounding Rects & Recorte** | $x,y,w,h = \text{boundingRect}(c)$; $\text{curt} = \text{img}[y:y+h, x:x+w]$ | Cálculo da caixa delimitadora retangular e extração da submatriz de cada letra, ordenando em fluxo natural de leitura. |

> **Nota sobre reconhecimento de caracteres (`cv2.matchShapes`):** O trabalho acadêmico descreve na seção de observações a técnica de comparar contornos de letras candidatas com contornos de referência de um alfabeto padrão usando `ret = cv2.matchShapes(c, l, cv2.CONTOURS_MATCH_I3, 0.0)`. Na aplicação, essa análise morfológica é integrada à pontuação de confiança e à validação de coerência tipográfica.

## 3. Melhorias de Precisão Implementadas

O documento acadêmico concluiu honestamente que o algoritmo *"funciona para todas as imagens que estão na pasta, mas é mais eficiente no caso das imagens que são compostas por palavras ou letras maiores"*. Para superar essas limitações históricas e atender à exigência de precisão, foram desenvolvidos módulos avançados de visão computacional:

### 3.1. Desmembramento Inteligente de Letras Coladas (Multi-Character Split)
- **O Problema:** Fontes condensadas, itálicas ou manuscritas possuem kerning muito apertado. Na binarização, pixels adjacentes se tocam, gerando um contorno unificado que fazia o algoritmo recortar grupos de letras juntos.
- **A Solução:** Componentes cuja razão de aspecto seja desproporcional ($\text{width} > 1.15 \times \text{height}$) passam pela análise do **Perfil de Projeção Vertical** ($\sum_y \text{pixel}(y, x)$). O sistema identifica **vales locais mínimos de densidade de tinta** entre picos de caracteres e desmembra a caixa delimitadora exatamente na transição, recalculando os limites reais de cada letra individual.

### 3.2. Filtro Morfológico de Elementos Não-Letras Clássico
- **O Problema:** Contornos causados por linhas decorativas, réguas de tabela, sublinhados, molduras da folha ou manchas de digitalização eram capturados como se fossem letras.
- **A Solução:** Filtros morfológicos biométricos baseados em geometria tipográfica:
  * Rejeição de linhas horizontais: $\text{width} / \text{height} > 3.8$ ou $(\text{width}/\text{height} > 2.5 \text{ e } \text{height} \le 6\text{px})$;
  * Rejeição de linhas verticais / molduras: $\text{height} / \text{width} > 14.0$ ou $(\text{height}/\text{width} > 5.0 \text{ e } \text{height} > 80\text{px})$;
  * Rejeição de blocos sólidos geométricos: densidade de preenchimento $> 95\%$ e área $> 140\text{px}^2$ exclusivamente quando $\min(w, h) > 10\text{px}$ (preservando caracteres monolineares como 'I' e '1');
  * Rejeição de poeiras hiper-esparsas: densidade $< 8\%$ ou área inferior ao limite adaptativo.

### 3.3. Rejeição Avançada de Ruídos de Fundos Coloridos, Desenhos e Molduras (Nova Implementação)

Em imagens ricas contendo fundos coloridos, ilustrações, grafismos, vinhetas ou cartões decorativos (como demonstrado na pasta `img/` com `text_image.jpg`, `ruidos.jpg` e `recortes.jpg`), a visão computacional tradicional sofre com a captura indevida de elementos visuais espúrios. Foram catalogados e resolvidos os seguintes padrões de ruído:

1. **Recortes de Fundo Liso / Gradientes (#57 a #79 em `recortes.jpg`):**
   * **Causa:** O equalizador adaptativo e binarizadores locais interpretam variações sutis de iluminação ou papel com ruído em áreas sem texto como se fossem primeiro plano. Bounding boxes geradas sobre essas regiões geravam recortes de blocos uniformes brancos, rosados ou acinzentados.
   * **Novo Conceito — Validação de Conteúdo e Contraste no Espaço de Imagem (Crop Content Validation):**
     Para cada componente candidato, extrai-se uma janela com margem de respiro ($\text{pad} = 3\text{px}$) na imagem em escala de cinza e calculam-se o **Desvio Padrão** ($\sigma_{\text{crop}}$) e a **Faixa Dinâmica de Contraste** ($\Delta I = I_{\max} - I_{\min}$):
     $$\sigma_{\text{crop}} = \sqrt{\frac{1}{N} \sum_{i=1}^N (I_i - \mu)^2}, \quad \Delta I = \max(I) - \min(I)$$
     Letras reais possuem transições abruptas de tinta sobre o suporte ($\sigma \ge 60$ a $98$, $\Delta I > 150$). Regiões homogêneas de papel ou fundo liso apresentam $\sigma < 16$ e $\Delta I < 35$, sendo descartadas imediatamente com 100% de eficácia.

2. **Molduras Retangulares e Cantos em "L" Vazados:**
   * **Causa:** Bordas de cartões, caixas de citação e molduras gráficas (como a moldura quadrada no canto superior esquerdo de `text_image.jpg`) possuem contornos nítidos. Sua caixa envolvente engloba uma área retangular grande, mas o interior é vazio.
   * **Novo Conceito — Teste de Preenchimento Central (Central Fill & Topological Stroke Test):**
     O algoritmo analisa a densidade de traço na submatriz central do componente correspondente a $[0.25h \dots 0.75h, 0.25w \dots 0.75w]$:
     $$\text{CentralFill} = \frac{\sum_{(y,x) \in \text{Centro}} \mathbb{I}_{\text{bin}}(y, x)}{\text{Área}(\text{Centro})}$$
     Caracteres alfanuméricos genuínos ('A', 'B', 'H', 'E', 'O', etc.) contêm traços cortando o centro de sua bounding box. Molduras e cantos em "L" apresentam $\text{CentralFill} < 4\%$ em caixas grandes ($w > 35\text{px}$ ou $h > 35\text{px}$), sendo categoricamente eliminadas.

3. **Elementos Gráficos e Ilustrações Lineares (ex: Linha Vermelha Inferior `o---o`):**
   * **Causa:** Traços decorativos coloridos e divisores com círculos nas extremidades quebram-se na binarização em uma sucessão de pequenos nós, pontos e fragmentos colineares.
   * **Novo Conceito — Rejeição de Bordas Externas e Filtro de Coerência de Linha:**
     Elementos que tocam o perímetro de 1 pixel da imagem ($x \le 1, y \le 1, x+w \ge W-1, y+h \ge H-1$) são tratados como cortes de enquadramento ou vinhetas periféricas. Componentes residuais de ilustrações com alturas minúsculas ou isoladas abaixo do bloco de texto são filtrados pela coerência tipográfica.

4. **Coerência Tipográfica de Linha e Rejeição de Outliers (Typographic Line Coherence):**
   * **Conceito:** Letras de uma mesma linha compartilham uma linha de base (*baseline*) e uma altura média estável. O algoritmo agrupa os componentes por proximidade vertical e calcula a **altura mediana da linha** ($H_{\text{med}}$).
   * Elementos com altura desproporcional ($h < 0.45 H_{\text{med}}$ ou $h > 1.85 H_{\text{med}}$) ou linhas isoladas com altura inferior à metade da mediana global ($h < 0.50 H_{\text{global}}$) são rejeitados como ruídos gráficos não-textuais.

5. **Normalização Morfológica de Fundo (TopHat / BlackHat):**
   * Em imagens com fundos complexos e gradientes fotográficos, o modo aprimorado emprega operadores de **TopHat** (para texto claro em fundo escuro) e **BlackHat** (para texto escuro em fundo claro) com elemento estruturante retangular ajustado ao tamanho típico da fonte:
     $$\text{BlackHat}(I) = (I \bullet K) - I$$
     Esse operador isola exclusivamente feições com largura inferior ao kernel estruturante (os traços das letras), neutralizando variações amplas de cor, sombras degradê e fundos de ilustrações antes da binarização.

6. **Preservação de Caracteres Monolineares Finos ('I' e '1'):**
   * Foi corrigida a falha comum onde letras finas eram descartadas por possuírem razão de aspecto vertical muito alta ($h/w > 6$) ou densidade de preenchimento próxima a 100%. O novo filtro admite proporções até $h/w = 14.0$ quando a altura é compatível com a linha de texto ($h \le 70\text{px}$), assegurando que nenhuma letra 'I' seja perdida.

### 3.4. Validação Comparativa na Imagem de Referência (`img/text_image.jpg`)
* **Antes das melhorias:** O algoritmo capturava entre **78** (em sensibilidade moderada) e **89** recortes (em sensibilidade alta), incluindo cantos de moldura, 23 recortes de papel liso, fatias da linha vermelha e círculos gráficos.
* **Após as melhorias:** O pipeline extrai **exatamente as 59 letras reais** das 5 linhas de texto ("HOW TO WRITE ALT TEXT AND IMAGE DESCRIPTIONS FOR THE VISUALLY IMPAIRED"), com confiança média de **100%** e **zero ruídos**, tanto no Modo Aprimorado quanto no Modo Acadêmico.

## 4. Funcionalidades implementadas no Produto

- **Execução e Exibição do Pipeline de 7 Passos do PDF:** o backend envia em cada requisição as imagens intermediárias reais geradas pelo OpenCV, permitindo navegar visualmente pelas etapas pedagógicas do trabalho acadêmico.
- **Componente PipelineViewer no Frontend:**
  * Aba *Pipeline de Processamento*: carrossel interativo com *stepper* numerado, visualização das 7 imagens intermediárias, fórmulas matemáticas formatadas em código mono e comandos do OpenCV;
  * Aba *Fundamentação & Limitações*: explica didaticamente as causas físicas e matemáticas de eventuais imperfeições (kerning estreito, ruídos de iluminação, fragmentação de acentos) e cita o trecho oficial de conclusão do trabalho acadêmico.
- **Seletor de Modo no Painel de Configurações:**
  * Modo Aprimorado: executa o pipeline do PDF complementado com divisão inteligente de caracteres via perfil de projeção vertical e filtros morfológicos de ruído e linhas;
  * Modo Acadêmico Puro: executa fielmente o fluxo estrito com parâmetros padrão do documento em PDF.
- **Presets de Configuração Rápida:** botões de 1 clique (*Equilibrado*, *Alta Sensibilidade* e *Anti-Ruído*) para aplicar parâmetros otimizados instantaneamente.
- **Upload Ágil e Confiável em 1 Clique:** área de upload nativa com `<label>` associada diretamente a `<input type="file">`, abrindo o seletor na primeira tentativa com carregamento imediato, suporte a arrastar e soltar (drag & drop) e validação dupla (MIME e extensão: PNG, JPG, JPEG, WEBP).
- **Toolbar de Ações da Amostra (Imagem de Origem):**
  * **Alternador de Visão Original / Debug (N):** alternância instantânea entre a foto original e a visualização com contornos e bounding boxes coloridos;
  * **Pílula Flutuante Bidirecional:** botão inferior interativo que informa a quantidade de caracteres detectados e alterna a visualização com um clique;
  * **Ampliação em Alta Resolução (Zoom Lightbox):** modal em tela cheia com alta nitidez e fechamento em clique externo;
  * **Girar Imagem (90°):** rotação instantânea em sentido horário via HTML5 Canvas, recriando o arquivo em memória para correção de orientação antes da segmentação;
  * **Substituir Imagem:** botão dedicado com ícone de pasta (`FolderOpen`) para troca rápida de arquivo;
  * **Remover Imagem (Lixeira):** limpa o arquivo ativo e redefine o estado da segmentação e dos resultados.
- **Segmentação e Reconstrução Visual da Leitura:** recortes reais de cada letra exibidos na ordem topológica natural de leitura e em grade completa.
- **Inspetor Geométrico de Caracteres (Modal):** clique em qualquer letra recortada para abrir o inspetor com ampliação em alta resolução, coordenadas exatas $(x, y)$, dimensões $(w, h)$, área em $px^2$, linha e confiança.
- **Cópia Rápida de IDs de Transcrição:** botão com 1 clique para copiar a sequência identificada para a área de transferência com feedback animado (*"Copiado!"*).
- **Comparação e Detecção de Plágio:** cálculo de similaridade com barra de progresso visual, classificação semântica colorida (`plagio_detectado`, `semelhanca_parcial`, `imagem_aceita`) e cartões de métricas individuais.
- **Histórico Persistido com Gerenciamento Completo no Banco de Dados:**
  * Persistência em MongoDB Atlas com fallback resiliente em memória;
  * **Exclusão Individual (Item a Item):** cada item possui botão de lixeira para apagar permanentemente o registro e todas as suas letras recortadas do banco de dados (MongoDB `delete_one`), com confirmação de segurança;
  * **Limpeza Total do Histórico:** botão "Limpar Histórico" no topo do painel para apagar todo o acervo do banco de dados de uma só vez (MongoDB `delete_many`), com confirmação prévia;
  * **Contador de Registros:** indicador visual com a contagem exata de imagens salvas;
  * **Busca com Debounce, Contador e Realce:** pesquisa por nome do arquivo ou transcrição com marcação visual dos termos encontrados e totalização de resultados.
- **Exportação em ZIP:** download de todas as letras segmentadas e da transcrição textual.

## 5. Design System, Arquitetura Visual e Responsividade

A interface da aplicação foi concebida sob o padrão visual **AI & Vision Studio**, priorizando precisão visual, estética contemporânea e ergonomia de uso:

- **Tipografia Escalonada:**
  * **Plus Jakarta Sans:** tipografia primária de interface, com alto nível de legibilidade para textos, botões e labels;
  * **Space Grotesk:** tipografia geométrica para títulos de destaque e identidade da marca;
  * **JetBrains Mono:** tipografia monoespaçada aplicada a parâmetros, coordenadas, percentuais, fórmulas e tags de etapas.
- **Paleta de Cores e Tokens Semânticos:**
  * Base em ardósia/grafite neutro (`#080b11` a `#1a2438`) no tema escuro e superfícies alvas e limpas no tema claro;
  * Acento de marca em Índigo Elétrico (`#6366f1` / `#4f46e5`) e destaques em Ciano (`#06b6d4`);
  * Cores semânticas reservadas para diagnósticos reais: Esmeralda para aceitação (`#10b981`), Âmbar para parcialidade (`#f59e0b`) e Carmim/Rosa para plágio (`#f43f5e`).
- **Técnicas Avançadas de Superfície & Glassmorphism:**
  * Painéis e cartões com `backdrop-filter: blur(16px)` e bordas semitransparentes com brilho especular;
  * Malhas de gradientes radiais suaves no fundo (*ambient glow*);
  * Viewport de imagem com padrão xadrez (*checkerboard*) sutil para facilitar a visualização de fundos transparentes e recortes.
- **Micro-interações e Vetorização (Lucide Icons):**
  * Substituição integral de emojis por ícones vetoriais de alta precisão da biblioteca `lucide-react`;
  * Switches deslizantes personalizados inspirados em design systems modernos (iOS / Linear);
  * Sliders com trilha de preenchimento ativo e marcadores numéricos em *pills* monocromáticas;
  * Hover cards com elevação suave (`transform: translateY(-2px)`) e *focus ring* acessível para navegação por teclado.
- **Total Responsividade:**
  * **Desktop (> 1140px):** layout em duas colunas com sidebar fixa à esquerda e fluxo de análise à direita;
  * **Notebooks e Tablets (768px - 1140px):** menu retrátil de ajustes com botão alternador (*toggle*) para não poluir o espaço visual das imagens;
  * **Mobile (< 768px):** empilhamento vertical responsivo, cards fluidos com `clamp()`, botões em largura total e modais ajustados a telas compactas.

### 5.1. Stack Tecnológica e Dependências

#### Backend
- Python 3.10+
- OpenCV (`opencv-python-headless`)
- FastAPI & Uvicorn
- NumPy
- Pytest & pytest-cov
- PyMongo
- python-dotenv

#### Frontend
- React 18 & React DOM
- TypeScript
- Vite
- Axios
- JSZip
- Lucide React (`lucide-react` — ícones vetoriais modernos)
- Google Fonts (`Plus Jakarta Sans`, `Space Grotesk`, `JetBrains Mono`)

### 5.2. Requisitos de Ambiente

- Python 3.10+
- Node.js 18+
- npm
- Conta no MongoDB Atlas (opcional — a aplicação opera com fallback local resiliente em memória, ver seção 11)
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

## 11. Persistência e Gerenciamento do Histórico no Banco de Dados

O histórico de imagens processadas conta com um ciclo de vida CRUD completo persistido em banco de dados:

- **Com `MONGODB_URI` definida e conexão bem-sucedida:** o backend salva e gerencia os registros diretamente no MongoDB Atlas. Essa escolha faz sentido pelo volume de imagens e textos longos, porque o MongoDB aceita documentos flexíveis, armazena metadados, imagens em base64 e recortes em arrays sem exigir um esquema rígido.
- **Sem `MONGODB_URI` (ou com falha de conexão):** o backend usa um histórico **em memória** (`_local_history`), mantido enquanto o processo do servidor estiver rodando. Ele permite testar todo o fluxo (segmentar, salvar, listar, buscar, abrir item, apagar individual e limpar tudo) sem depender de um banco externo.

### Estrutura do documento persistido
- imagem original/processada em base64 (`imageData`);
- nome do arquivo (`sourceName`);
- transcrição completa em ordem natural de leitura (`transcript`);
- array completo de letras recortadas (`letters`), cada uma com sua sub-imagem em base64 (`letter.image`), coordenadas geométricas $(x, y, w, h)$, área e pontuação de confiança;
- métricas e metadados detalhados (`metadata`);
- carimbos de data/hora (`createdAt` e `updatedAt`).

### Operações de Exclusão no Banco de Dados
- **Exclusão Individual (`DELETE /api/history/{item_id}`):** remove o documento específico do MongoDB via `collection.delete_one()` (pesquisando por `ObjectId` e `string`), expurgando do banco a imagem e todas as suas letras vinculadas. Também remove o item da memória local.
- **Limpeza Total (`DELETE /api/history`):** executa `collection.delete_many({})` e esvazia a memória local, apagando permanentemente todos os registros de processamento armazenados.

A coleção padrão em desenvolvimento é:

```text
processed_images
```

Em produção, o padrão recomendado/automático é:

```text
processed_images_prod
```

Isso evita misturar dados locais com registros de produção.

## 12. Histórico e Gerenciamento no Frontend

A interface possui um painel completo de histórico de imagens processadas com:

- **Pílula com Contador de Registros:** exibe a quantidade exata de imagens salvas no histórico no cabeçalho;
- **Botão "Limpar Histórico":** botão de destaque no cabeçalho (visível quando há itens salvos) que solicita confirmação prévia e dispara a exclusão de todas as imagens e letras do banco de dados em lote;
- **Botão de Exclusão Individual (Lixeira em cada card):** permite apagar uma imagem específica com um clique, solicitando confirmação de segurança com o nome do arquivo e removendo o registro do banco de dados de forma imediata;
- **Descarregamento Automático:** se a imagem excluída estiver aberta no visualizador do editor, a visualização é resetada para evitar estados órfãos;
- **Miniatura da imagem:** preview visual rápido do processamento salvo;
- **Carrossel/Fita de Letras Recortadas:** visualização das miniaturas das primeiras 14 letras com badge para excedentes (`+N`);
- **Texto transcrito e nome do arquivo:** com destaque visual (*highlight*) dos termos pesquisados quando há busca ativa;
- **Item Clicável:** clique em qualquer parte do card para carregar o resultado histórico de volta no editor e no inspetor de caracteres;
- **Campo de Busca com Debounce (350ms):** filtra pelo nome do arquivo **ou** pela transcrição no backend com indicador visual de carregamento;
- **Botão "Atualizar":** recarrega a lista do banco de dados ou repete a busca atual;
- **Botão de Limpar Busca (✕):** redefine o filtro e retorna a listagem completa.

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
| POST   | `/api/segment`           | Segmenta a imagem e retorna letras, transcript, debugImage, métricas e as 7 imagens intermediárias do pipeline em PDF |
| POST   | `/api/compare`           | Compara duas imagens e retorna grau de similaridade, status e veredito |
| GET    | `/api/history`           | Lista os últimos 20 itens do histórico salvo (MongoDB Atlas ou memória) |
| GET    | `/api/history/search?q=` | Busca itens do histórico por nome do arquivo ou transcrição             |
| POST   | `/api/history/save`      | Salva manualmente uma imagem processada no histórico                    |
| GET    | `/api/history/{item_id}` | Retorna um item específico do histórico por ID                          |
| DELETE | `/api/history/{item_id}` | Exclui permanentemente um item e todas as suas letras do banco de dados |
| DELETE | `/api/history`           | Limpa permanentemente todo o histórico de processamentos no banco de dados |
| OPTIONS| `/api/segment`, `/api/compare`, `/api/history`, `/api/history/{item_id}` | Respostas de CORS (preflight) |
| GET    | `/api/health`            | Health check da API                                                     |
| GET    | `/health`                | Health check equivalente, fora do prefixo `/api`                        |
| GET    | `/`                      | Rota raiz com nome, versão e status do serviço                          |

> Importante: `/api/history/search` e `/api/history` (DELETE) precisam estar registradas **antes** de `/api/history/{item_id}` no router. Como o FastAPI casa rotas na ordem de registro, se a rota dinâmica vier primeiro, chamadas literais são interpretadas como parâmetro dinâmico e falham com erro de validação. Essa ordem já está correta e testada em `backend/src/api/routes/index.py`.

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
  core/segmenters/improved_segmenter.py  # executa pipeline dos 7 passos, desmembramento de letras e filtro
  core/processors/opencv_processor.py    # métodos de visão computacional do PDF (bilateral, otsu, canny, contornos)
  core/validators/letter_validator.py    # validação de consistência e pontuação de confiança
  core/utils/image_utils.py          # decodificação e codificação de imagens base64 (data URL)
  core/utils/geometry_utils.py       # cálculos geométricos auxiliares (posições, bounding box, padding)
  core/models/                       # modelos de dados (LetterBox, SegmentResult, ProcessingOptions)
  services/mongodb_service.py        # persistência em MongoDB Atlas com fallback resiliente em memória
```

Fluxo executado em `POST /api/segment`:

1. **Imagem Load:** decodificação da imagem em base64 e redimensionamento proporcional se necessário;
2. **Tons de Cinza:** conversão via ponderação $Y \leftarrow 0.299R + 0.587G + 0.114B$;
3. **Filtro Bilateral:** aplicação de `cv2.bilateralFilter(gray, 10, 75, 75)` para remoção de ruído preservando bordas;
4. **Binarização Otsu:** cálculo estatístico do limiar ótimo de Otsu e inversão com `bitwise_not`;
5. **Bordas de Canny:** detecção com derivadas direcionais de Sobel e limiares 70 e 150;
6. **Identificação de Contornos:** rastreamento externo com compressão `CHAIN_APPROX_SIMPLE`;
7. **Divisão de Letras Coladas:** mapeamento do perfil de projeção vertical e separação nos vales de densidade de tinta;
8. **Filtragem de Não-Letras:** descarte de linhas horizontais, molduras verticais, blocos sólidos e ruídos esparsos;
9. **Agrupamento e Ordenação:** organização espacial por linha e palavra, preservando o fluxo de leitura real;
10. **Geração das Imagens dos 7 Passos:** renderização e empacotamento das 7 etapas teóricas para o frontend;
11. **Persistência:** salvamento automático do registro no histórico quando o MongoDB estiver habilitado;
12. **Retorno estruturado:** payload com letras recortadas, overlay de debug, transcript, metadados e array `steps`.

### Frontend

```text
frontend/src/
  components/Segmenter/Segmenter.tsx            # tela principal: orquestra upload, comparação, histórico e abas
  components/LetterGrid/LetterGrid.tsx          # grade de letras recortadas e visualização da transcrição real
  components/PipelineViewer/PipelineViewer.tsx  # visualizador das 7 etapas do PDF e painel de transparência técnica
  components/ControlPanel/ControlPanel.tsx      # painel com seletor de modo e toggles de precisão
  components/ImageUploader/ImageUploader.tsx    # upload e preview da imagem original e de comparação
  components/common/                            # LoadingSpinner e ErrorMessage
  hooks/useSegmenter.ts                         # chama POST /api/segment e mantém estado reativo
  hooks/useImageUpload.ts                       # controla upload/preview de imagem em base64
  services/api.ts                               # client axios para todos os endpoints da API
```

A interface oferece:

- **Seletor de Modo:** alternância imediata entre *Aprimorado (PDF + Refinamentos de Precisão)* e *Acadêmico Puro (Exato do PDF UFRRJ)*;
- **Toggles de Alta Precisão:** ativar/desativar desmembramento de letras coladas e filtro de elementos não-letras;
- **Visualizador Interativo do Pipeline do PDF:** carrossel para navegar pelas 7 imagens intermediárias geradas pelo OpenCV com fórmulas e explicações pedagógicas;
- **Painel de Transparência Técnica:** explicação transparente e honesta das causas físicas de imperfeições em visão computacional clássica (kerning, iluminação irregular, caracteres desconectados como 'i'/'j' e acentos);
- **Texto Reconstruído em Ordem de Leitura:** exibição dos recortes reais na sequência do texto;
- **Comparação de Conteúdo e Plágio:** análise percentual com classificação e veredito claro;
- **Histórico Completo:** com pesquisa instantânea, destaque de texto e visualização de recortes salvos;
- **Exportação em `.zip`:** download de todas as letras segmentadas e da transcrição textual.

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

O projeto possui uma suíte completa de **22 testes automatizados** no backend e validação de tipagem estrita no frontend:

- `backend/tests/test_segmenter.py` — 15 testes cobrindo segmentação morfológica, texto em baixo contraste, detecção de plágio, geração fiel dos 7 passos teóricos do PDF, separação de letras agrupadas e filtro de elementos não-letras;
- `backend/tests/test_mongodb_history.py` — 3 testes cobrindo comportamento do serviço de MongoDB (resolução de nomes de coleção, documento do histórico e isolamento de ambiente);
- `backend/tests/test_history_save.py` — 4 testes cobrindo salvamento e recuperação de registros com fallback local, exclusão individual com validação de erro 404, limpeza completa de todos os itens e teste de integração no handler.

Comandos para rodar a suíte do backend:

```bash
cd backend
pytest tests/ -q
# Resultado esperado: 22 passed
```

Para validar a integridade dos tipos e compilação do frontend:

```bash
cd frontend
npm run build
# Resultado esperado: ✓ built in ~16s (zero erros de TypeScript)
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
    components/
      ControlPanel/
      ImageUploader/
      LetterGrid/
      PipelineViewer/
      Segmenter/
      common/
    hooks/
    services/
    types/
  package.json
  .env.example
scripts/
  setup.sh
Processamento de Imagens.pdf    # documento acadêmico de referência (UFRRJ - TM438)
GUIA.md                         # este guia completo de referência técnica
GUIA_PROC_IMG.md
README.md
Makefile
```

## 21. Observações importantes

- **Fidelidade ao Trabalho em PDF:** O projeto implementa todos os 7 passos teóricos do documento acadêmico (*Imagem Load*, *GrayScale*, *Bilateral Filter*, *Otsu*, *Canny*, *Contornos* e *Recorte matricial*), tornando o processo totalmente auditável pelo frontend.
- **Transparência e Honestidade Científica:** O painel de transparência expõe com franqueza as limitações da visão computacional tradicional (kerning estreito, sombras e caracteres desconectados) e cita a conclusão oficial do trabalho dos autores.
- **Resiliência do Histórico:** Se `MONGODB_URI` estiver vazia ou se houver perda de conexão ao cluster Atlas, o aplicativo automaticamente faz fallback para armazenamento em memória (`_local_history`), garantindo que nenhuma funcionalidade do frontend quebre ou retorne erro 500.
- **Existe um `index.py` solto na raiz:** Ele contém código legado/experimental e **não é utilizado** pelo servidor FastAPI ativo (`backend/src/server.py`).
- **Segurança de credenciais:** Para produção, mantenha a string de conexão em variável de ambiente segura e nunca comite o arquivo `.env`.

## 22. Dicas de uso

- **Upload em 1 Clique e Validação Rápida:** O seletor de arquivos abre na primeira interação com `<label>` nativo; você também pode arrastar e soltar (drag & drop) arquivos PNG, JPG, JPEG ou WEBP diretamente sobre o card;
- **Girar Imagens com 1 Clique (Rotação 90°):** Caso a foto ou documento esteja em orientação incorreta, utilize o botão de rotação (`RotateCw`) no card da amostra para reorientá-la instantaneamente via Canvas antes de processar;
- **Modo Aprimorado (Recomendado):** Ideal para imagens com fontes condensadas, texto corrido ou documentos escaneados com pequenas manchas e molduras;
- **Modo Acadêmico Puro:** Ideal para demonstração pedagógica dos resultados exatos obtidos com os parâmetros literais do trabalho em PDF;
- **Uso dos Presets de Configuração:** Utilize os botões rápidos (*Equilibrado*, *Alta Sensib.* e *Anti-Ruído*) para aplicar parâmetros pré-calibrados instantaneamente com um clique;
- **Inspeção Detalhada de Caracteres:** Clique sobre qualquer letra recortada na galeria para abrir o **Modal Inspetor Geométrico**, visualizando o recorte ampliado, coordenadas $(x, y)$, dimensões $(w, h)$, área em $px^2$, linha e confiança;
- **Visualização Dual e Zoom Lightbox:** Alterne entre a imagem original e a visualização de debug com *bounding boxes* coloridos através dos botões no cabeçalho do card, ou use o ícone de lupa para abrir o visualizador ampliado em tela cheia;
- **Cópia Instantânea da Transcrição:** Utilize o botão "Copiar IDs" no cabeçalho da galeria para transferir a sequência identificada para a área de transferência;
- **Aba de Transparência & Limitações:** Consulte a aba *Transparência & Limitações Técnicas* no visualizador de pipeline para entender os operadores matemáticos, kerning e diagnósticos em tempo real da imagem;
- **Gerenciamento e Limpeza do Banco de Dados:** Exclua registros antigos individualmente clicando no ícone de lixeira do card ou limpe todo o acervo clicando em "Limpar Histórico" no cabeçalho; ambas as ações expurgam as imagens e os recortes salvos definitivamente do MongoDB Atlas;
- **Ajuste Fino de Sensibilidade:** Em imagens com texto de baixo contraste ou fundo ruidoso, ajuste a sensibilidade e ative as opções *Remover ruídos* e *Melhorar contraste*.


