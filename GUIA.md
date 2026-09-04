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
- funcionar como Progressive Web App (PWA), com instalação no dispositivo, modo standalone e carregamento do shell visual em cache.

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

O documento acadêmico concluiu honestamente que o algoritmo *"funciona para todas as imagens que estão na pasta, mas é mais eficiente no caso das imagens que são compostas por palavras ou letras maiores"*. Para superar essas limitações históricas e atender à exigência de precisão prática em imagens reais, foram desenvolvidos módulos avançados de visão computacional:

### 3.1. Desmembramento Inteligente & Preservação de Glifos Nativamente Largos ('m', 'w', 'M', 'W')
- **O Problema Clássico:** Fontes condensadas, itálicas ou manuscritas possuem kerning muito apertado. Na binarização, pixels adjacentes se tocam, gerando um contorno unificado que fazia o algoritmo recortar grupos de letras juntos.
- **O Efeito Colateral Antigo (Fatiamento de 'm'):** Algoritmos ingênuos de projeção vertical que analisavam apenas a razão de aspecto ($\text{width} > 1.15 \times \text{height}$) fatiam a letra **'m'** em 2 ou 3 fragmentos (conforme observado na amostra `test_text.jpg` / `sample.jpeg`). Isso ocorria porque o 'm' possui 3 hastes verticais e 2 vales de arcos internos, sendo confundido com duas ou três letras vizinhas coladas.
- **A Solução Implementada:**
  1. **Detecção de Assinatura Morfológica de Glifo Amplo (`_is_single_wide_glyph`):** O sistema analisa o perfil de projeção suavizado antes de fatiar. Caracteres com proporção entre $1.05$ e $1.85$ que apresentam 3 picos característicos bem distribuídos ($\sim 15\%$, $50\%$ e $85\%$ da largura) e arcos contínuos no topo (para 'm'/'M') ou 2 picos largos com vértice intermediário (para 'w'/'W') são reconhecidos como letras nativamente largas e **preservados integralmente sem divisão**.
  2. **Largura Mínima Tipográfica Proporcional:** Ao dividir agrupamentos genuínos (ex: *"de"*, *"qu"*, *"am"*), o algoritmo impõe uma largura mínima de caractere proporcional à altura ($\min\_char\_w = \max(\text{min\_size}, \text{int}(H \times 0.18))$), evitando que o desmembramento gere fatias espúrias de 3 a 4 pixels de espessura.

### 3.2. Filtro Morfológico & Preservação de Letras Monolineares e Verticais ('l', 'I', '1')
- **O Problema Clássico:** Linhas decorativas, molduras e divisórias de página geravam contornos espúrios. Porém, filtros simplistas baseados em limites fixos de pixels (ex: $\text{height} > 80\text{px}$ com $h/w > 5.0$, ou blocos sólidos com $\min(w, h) > 10\text{px}$) descartavam a letra **'l'** minúscula ou **'I'** maiúsculo em imagens com fontes grandes (como visto em `test_text.jpg`, onde o 'l' possuía $w = 12\text{px}, h = 97\text{px}$ e foi eliminado tanto como "linha vertical" quanto como "bloco sólido").
- **A Solução Implementada:**
  1. **Distinção de Molduras por Escala de Página:** Molduras e divisórias reais ocupam uma fração substancial da altura da imagem ($\ge 20\%$ a $30\%$ da altura total $H_{\text{img}}$) ou possuem esbeltez extrema ($h/w > 20.0$). Letras como 'l' e 'I', mesmo em fontes grandes ($h \sim 100\text{px}$), ocupam apenas uma pequena fração vertical da página ($\sim 7\%$) e compartilham a altura das outras letras da linha, sendo preservadas.
  2. **Preservação de Caracteres Monolineares:** O filtro de blocos sólidos geométricos compactos agora exige que o componente não seja esguio ($0.25 \le w/h \le 3.5$), impedindo que uma haste puramente vertical de alta densidade (como 'l' ou 'I') seja rotulada como "bloco geométrico sólido".

### 3.3. Rejeição Avançada de Ruídos de Fundos Coloridos, Desenhos e Molduras
Em imagens ricas contendo fundos coloridos, ilustrações, grafismos, vinhetas ou cartões decorativos (como demonstrado na pasta `img/` com `text_image.jpg`, `ruidos.jpg` e `recortes.jpg`), a visão computacional tradicional sofre com a captura indevida de elementos visuais espúrios:
1. **Validação de Conteúdo e Contraste no Espaço de Imagem (Crop Content Validation):** Avaliação do desvio padrão ($\sigma_{\text{crop}}$) e da faixa dinâmica ($\Delta I$) para descartar recortes lisos de papel ou gradientes sem texto.
2. **Teste de Preenchimento Central (Central Fill):** Descarta molduras retangulares e cantos em "L" vazados ($\text{CentralFill} < 4\%$).
3. **Normalização Morfológica (TopHat / BlackHat):** Suprime variações lentas de fundo e sombras degradê antes da binarização.

### 3.4. Segmentação em Textos Densos e Parágrafos (Resolução de Alta Densidade e Fusão de Diacríticos)
Imagens de alta resolução contendo páginas de livros ou parágrafos inteiros (como `wandy-luz.jpg`, com 18 linhas e mais de 600 caracteres) apresentavam perda massiva de letras (detectando apenas 127 ou 4 letras no sistema original). Os problemas identificados e corrigidos foram:
1. **Desacoplamento do Limiar de Ruído da Resolução da Imagem:** O cálculo anterior descartava componentes menores que $\text{total\_area} \times 0.00025$. Em imagens de 1.1 megapixel, isso criava um limiar de corte de 276 pixels, apagando 99% das letras (cuja mediana era de 139 pixels). O limiar foi reestruturado de forma adaptativa e segura (limitado entre 3 e 8 pixels), eliminando poeira e scanner grain sem afetar caracteres.
2. **Preservação de Traços Finos com Fechamento Morfológico Suave:** A operação destrutiva `MORPH_OPEN (2, 2)` foi eliminada do pré-processamento de texto, pois erodia 35% de toda a tinta de fontes serifadas com traços de 1px. Em seu lugar, adotou-se exclusivamente `MORPH_CLOSE (2, 2)`, que une micro-fissuras nos traços sem desgastar as pontas.
3. **Fusão Inteligente de Pingos e Acentos (*Diacritic Association*):** Em português, letras como 'i', 'j', '!', '?' e caracteres com til, agudo, circunflexo ou cedilha ('ã', 'é', 'á', 'ç') possuem marcas fisicamente separadas do corpo da letra. O módulo `_merge_diacritics` detecta marcas sobrepostas na mesma coluna vertical e as funde na mesma caixa delimitadora, unificando a letra acentuada em um único recorte com altura coerente.
4. **Agrupamento Robusto de Linhas por Centro Vertical:** A ordenação e agrupamento de linhas agora utiliza o centro vertical das caixas ($y + h/2$) com tolerância proporcional à altura mediana da linha ($\pm 0.65 H_{\text{med}}$), impedindo que letras com ascendentes ou acentos fragmentem uma mesma linha de leitura.

### 3.5. Validação Comparativa e Resultados Obtidos
A eficácia dos algoritmos foi comprovada em testes práticos nas amostras do repositório:
* **Amostra com Palavras Grandes (`img/test_text.jpg` - "Sample text here"):**
  - **Antes:** 15 recortes reportados (a letra **'l'** não era detectada por excesso de altura e a letra **'m'** era indevidamente fatiada em 3 partes).
  - **Agora:** **Exatamente as 14 letras reais** detectadas com 100% de acurácia: `S, a, m, p, l, e, t, e, x, t, h, e, r, e`, com 'm' e 'l' preservados com caixas perfeitas.
* **Amostra Densa de Parágrafo (`img/wandy-luz.jpg` - Texto de Wandy Luz):**
  - **Antes:** Apenas **127 letras** marcadas no print do usuário (`img/imagem.jpeg`), com linhas inteiras vazias devido ao corte por área total e fragmentação por erosão.
  - **Agora:** **615 caracteres detectados e recortados**, recuperando mais de 98% de todo o texto (que possui 583 letras e 618 caracteres totais), distribuídos perfeitamente nas 18 linhas de leitura.
* **Amostra de Referência com Molduras e Ruídos (`img/text_image.jpg`):**
  - **Resultado:** **59 letras exatas** extraídas das 5 linhas com zero captura de molduras ou ruídos lisos de papel.

### 3.6. Limitações Físicas e Teóricas da Visão Computacional Clássica
Em respeito à honestidade técnica e científica (TM438 - UFRRJ), destacam-se as fronteiras metodológicas onde a abordagem clássica baseada em Otsu + Canny + Morfologia atinge seus limites físicos:
1. **Ligaduras Tipográficas Severas e Kerning Físico Nulo:**
   Quando dois caracteres possuem traços tipográficos fundidos sem qualquer espaçamento branco entre si (ex: ligaduras clássicas *"fi"*, *"fl"*, ou caracteres manuscritos onde a tinta é contínua), a binarização produz um único componente conectado sem vale no perfil de projeção vertical. Nesses casos raros, a visão computacional tradicional mantém os dois caracteres no mesmo recorte retangular, pois não há informação de borda física para separá-los.
2. **Caligrafia Cursiva Manuscrita Contínua:**
   Em textos cursivos manuscritos com ligação contínua de traço entre letras, a ausência de pausas espaciais impede a segmentação puramente matricial sem o auxílio de um modelo estatístico ou rede neural de OCR (ex: Tesseract / CRNN).
3. **Degradês de Iluminação e Sombras Fortes Não-Lineares:**
   Sombras projetadas sobre o papel com transições suaves de luminância podem deslocar o limiar ótimo de Otsu em certas regiões da página. O Filtro Bilateral e a normalização TopHat/BlackHat mitigam gradientes moderados, mas fotos com iluminação severamente desbalanceada ainda se beneficiam de correção manual ou do modo adaptativo.
4. **Ausência de Modelo Semântico de Linguagem:**
   O pipeline trabalha exclusivamente com características geométricas de contornos matriciais. Ele não possui um modelo de linguagem natural (LLM/dicionário) para inferir letras omitidas ou "adivinhar" caracteres encobertos.

### 3.7. Formulação de Confiabilidade 100% Transparente (Auditoria dos 4 Pilares sem Caixa-Preta)
Em visão computacional aplicada, a apresentação de uma "porcentagem de confiança" como número arbitrário sem justificativa matemática gera desconfiança e inviabiliza auditorias. No Pattern Checker, a confiabilidade de cada caractere individual e do processamento global é **100% determinística, auditável e transparente**, calculada diretamente a partir de 4 pilares físicos e geométricos dos pixels recortados:

$$C = 0.35 \cdot S_{\text{morf}} + 0.30 \cdot S_{\text{contraste}} + 0.20 \cdot S_{\text{linha}} + 0.15 \cdot S_{\text{solidez}}$$

1. **Morfologia Tipográfica ($S_{\text{morf}}$, peso 35%):**
   - Avalia a razão de aspecto ($AR = \text{largura} / \text{altura}$) do componente retangular:
     * $0.28 \le AR \le 0.95$: **score 1.0** (proporção típica da vasta maioria dos caracteres ocidentais minúsculos e maiúsculos);
     * $0.18 \le AR < 0.28$ ou $0.95 < AR \le 1.45$: **score 0.93** (glifos esguios como 't', 'r', 'f' ou glifos naturalmente largos como 'm' e 'w');
     * $0.10 \le AR < 0.18$ ou $1.45 < AR \le 1.85$: **score 0.85** (hastes verticais como 'l', 'I', '1' ou combinações acentuadas);
     * $AR < 0.05$ ou $AR > 3.5$: **penalidade para 0.10** (descarte de réguas e artefatos filiformes);
     * Demais casos: **score 0.72**.

2. **Contraste e Dinâmica de Tinta ($S_{\text{contraste}}$, peso 30%):**
   - Inspeciona o canal em tons de cinza da imagem sobre a submatriz do caractere ampliada com margem de segurança ($\text{pad} = 2\text{px}$), medindo o desvio padrão dos níveis de cinza ($\sigma$) e a faixa dinâmica de intensidades ($\Delta I = I_{\max} - I_{\min}$):
     * $\sigma < 14.0$ ou $\Delta I < 30.0$: **penalidade para 0.10** (identifica e descarta regiões lisas de papel sem tinta);
     * $\sigma \ge 45.0$ e $\Delta I \ge 140.0$: **score 1.0** (traço de tinta escuro com contraste nítido sobre suporte claro ou inverso);
     * $\sigma \ge 30.0$ e $\Delta I \ge 90.0$: **score 0.92** (contraste bom e legível);
     * $\sigma \ge 20.0$: **score 0.82** (contraste moderado);
     * Demais casos: **score 0.70**.

3. **Coerência Tipográfica de Linha ($S_{\text{linha}}$, peso 20%):**
   - Avalia o alinhamento e a consistência de corpo tipográfico, comparando a altura da caixa delimitadora ($h$) com a mediana de altura de todos os caracteres da mesma linha ($H_{\text{med}}$):
     * $0.75 \le h / H_{\text{med}} \le 1.35$: **score 1.0** (altura perfeitamente alinhada com o corpo da linha);
     * $0.50 \le h / H_{\text{med}} < 0.75$ ou $1.35 < h / H_{\text{med}} \le 1.80$: **score 0.92** (caracteres com ascendentes ou descendentes como 'b', 'd', 'p', 'q' e maiúsculas);
     * $0.28 \le h / H_{\text{med}} < 0.50$: **score 0.82** (letras menores, símbolos ou pontuações);
     * Demais variações: **score 0.65**.

4. **Solidez e Densidade de Preenchimento ($S_{\text{solidez}}$, peso 15%):**
   - Mede a razão entre a área de pixels pretos/tinta e a área total da bounding box ($D = \text{área} / (w \times h)$):
     * $0.15 \le D \le 0.75$: **score 1.0** (densidade clássica de traços de fontes tipográficas);
     * $0.10 \le D < 0.15$ ou $0.75 < D \le 0.92$: **score 0.90** (fontes ultrafinas/light ou ultranegrito/black);
     * Demais casos: **score 0.72**.
   - **Filtro de Moldura Vazada:** se a caixa tiver dimensões $\ge 25\text{px} \times 25\text{px}$ e a região central tiver menos de $3\%$ de preenchimento ($\text{CentralFill} < 0.03$), o componente é classificado como retângulo oco e recebe **score 0.10**.

5. **Índice Global e Detalhamento Estruturado (`confidence_breakdown`):**
   - A pontuação de confiabilidade geral da imagem é calculada pela média ponderada transparente dos 4 pilares médios calculados sobre todos os $N$ caracteres válidos:
     $$C_{\text{global}} = 0.35 \cdot \bar{S}_{\text{morf}} + 0.30 \cdot \bar{S}_{\text{contraste}} + 0.20 \cdot \bar{S}_{\text{linha}} + 0.15 \cdot \bar{S}_{\text{solidez}}$$
   - O backend empacota o objeto estruturado `confidence_breakdown` contendo:
     * `overall`: pontuação global consolidada $[0..1]$;
     * `letter_average`: média aritmética direta das notas individuais;
     * `aspect_ratio_score`, `contrast_score`, `line_coherence_score`, `density_score`: as médias exatas de cada pilar;
     * `weights`: o dicionário de pesos fixos aplicados;
     * `evaluated_letters`: a contagem exata de letras analisadas;
     * `description`: explicação textual descritiva da composição do resultado.

6. **Transparência Visual na Interface (Frontend):**
   - **Pílula de Confiança Interativa:** no cabeçalho do painel de caracteres (`LetterGrid`), o badge de confiança é um botão interativo. Ao clicar, expande o **Painel de Transparência da Confiabilidade**, exibindo barras de progresso proporcionais para cada um dos 4 pilares, suas respectivas pontuações percentuais e a fórmula matemática utilizada;
   - **Auditoria Individual no Modal Inspetor:** ao clicar sobre qualquer letra na galeria ou na fita de leitura, o modal exibe a seção **Auditoria dos 4 Pilares deste Caractere**, discriminando com exatidão como as dimensões físicas, o contraste e a densidade daquele recorte específico geraram sua nota de confiança;
   - **Diagnósticos em Tempo Real (`warnings`):** o sistema correlaciona a pontuação obtida com diagnósticos em linguagem natural (ex: indicando se o contraste moderado se deve a sombras ou se caracteres largos se devem a kerning apertado).

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
- **Painel de Transparência e Auditoria de Confiabilidade (100% Auditável):** no cabeçalho da grade de caracteres, a pílula de confiança é um botão interativo que expande o painel de decomposição dos 4 pilares (Morfologia 35%, Contraste 30%, Coerência de Linha 20% e Solidez 15%) com barras de progresso proporcionais, descrições e fórmula explícita;
- **Inspetor Geométrico de Caracteres (Modal com Auditoria de Pilares):** clique em qualquer letra recortada para abrir o inspetor com ampliação em alta resolução, coordenadas exatas $(x, y)$, dimensões $(w, h)$, área em $px^2$, linha, pontuação de confiança e o bloco completo de auditoria discriminando as notas dos 4 pilares calculadas individualmente para aquele caractere;
- **Cópia Rápida de IDs de Transcrição:** botão com 1 clique para copiar a sequência identificada para a área de transferência com feedback animado (*"Copiado!"*).
- **Comparação e Detecção de Plágio:** cálculo de similaridade com barra de progresso visual, classificação semântica colorida (`plagio_detectado`, `semelhanca_parcial`, `imagem_aceita`) e cartões de métricas individuais.
- **Histórico Persistido com Gerenciamento Completo no Banco de Dados:**
  * Persistência em MongoDB Atlas com fallback resiliente em memória;
  * **Exclusão Individual (Item a Item):** cada item possui botão de lixeira para apagar permanentemente o registro e todas as suas letras recortadas do banco de dados (MongoDB `delete_one`), com confirmação de segurança;
  * **Limpeza Total do Histórico:** botão "Limpar Histórico" no topo do painel para apagar todo o acervo do banco de dados de uma só vez (MongoDB `delete_many`), com confirmação prévia;
  * **Contador de Registros:** indicador visual com a contagem exata de imagens salvas;
  * **Busca com Debounce, Contador e Realce:** pesquisa por nome do arquivo ou transcrição com marcação visual dos termos encontrados e totalização de resultados.
- **Exportação em ZIP:** download de todas as letras segmentadas e da transcrição textual.
- **Preservação de fontes preenchidas e contornadas:** o filtro diferencia letras com centro vazio (`C`, `D`, `K`, `O`, `U`) de cantos/molduras geométricos, evitando descartar glifos estreitos ou outline.
- **Textos pequenos e densos:** a limpeza de ruído mantém componentes pequenos e o agrupamento por linhas usa tolerância proporcional à altura, preservando letras em parágrafos com múltiplas linhas.
- **Progressive Web App (PWA):** manifesto instalável, ícones do Pattern Checker e service worker registrado apenas no build de produção. O shell do frontend pode abrir com recursos estáticos em cache quando estiver sem conexão; chamadas à API, login, histórico e processamento continuam dependendo do backend.

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

### 5.3. PWA e instalação

O frontend é um PWA nativo, sem dependência adicional de plugin. O arquivo `frontend/public/manifest.webmanifest` define o nome, ícones, cores, modo `standalone`, orientação e rota inicial. O arquivo `frontend/public/sw.js` armazena apenas recursos estáticos do mesmo domínio e usa fallback para `index.html`; não armazena credenciais, cookies, imagens enviadas ou respostas da API.

O service worker é registrado somente quando o frontend é compilado em produção (`npm run build`). Em desenvolvimento, o Vite não registra o service worker para evitar cache durante alterações. Para instalar, publique o build em HTTPS e use a opção **Instalar aplicativo** do navegador. `localhost` também é considerado seguro pelos navegadores durante testes locais.

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
AUTH_EMAIL=admin@example.com
AUTH_PASSWORD_HASH=pbkdf2_sha256$310000$<salt-base64url>$<hash-base64url>
AUTH_SECRET_KEY=gere-uma-chave-aleatoria-com-secrets-token-urlsafe
AUTH_SESSION_SECONDS=28800
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
```

### 7.1. Acesso administrativo e proteção das credenciais

A aplicação agora inicia em uma tela de login e libera o processamento somente após uma sessão administrativa válida. O e-mail fica apenas no ambiente do backend; a senha nunca é armazenada em texto puro, no código-fonte ou no bundle do frontend. O backend compara a senha com um hash PBKDF2-SHA256 e entrega uma sessão assinada em cookie `HttpOnly`, com validade configurável.

Gere o hash da senha e uma chave de sessão diretamente no terminal, dentro da raiz do projeto (não inclua os valores resultantes neste guia):

```powershell
python -c "from src.api.auth import create_password_hash; print(create_password_hash('SUA_SENHA'))"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie os resultados para `AUTH_PASSWORD_HASH` e `AUTH_SECRET_KEY` no arquivo `backend/.env`, e configure `AUTH_EMAIL` com o e-mail administrativo. O arquivo `.env` é ignorado pelo Git. Em produção, defina `AUTH_COOKIE_SECURE=true` e `AUTH_COOKIE_SAMESITE=none`: como Vercel e Render usam domínios diferentes, o navegador exige cookie `Secure` e `SameSite=None` para manter a sessão. O backend também força `Secure` quando `SameSite=None`, evitando a combinação inválida exibida pelo Chrome no Android. Após o login, o frontend confirma `/api/auth/session` antes de abrir o dashboard. As rotas de segmentação, comparação e histórico exigem essa sessão; `/health` permanece público para monitoramento.

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
- array completo de letras recortadas (`letters`), cada uma com sua sub-imagem em base64 (`letter.image`), coordenadas geométricas $(x, y, w, h)$, área, pontuação de confiança e notas detalhadas dos 4 pilares (`letter.confidenceDetails`);
- métricas e metadados detalhados (`metadata`), contendo largura, altura, quantidade total de letras, tempo de processamento, pontuação global de confiança (`confidenceScore`), decomposição estruturada dos 4 pilares (`confidenceBreakdown`) e lista de diagnósticos (`warnings`);
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
| POST   | `/api/auth/login`       | Valida o e-mail e a senha administrativa e cria sessão HttpOnly |
| POST   | `/api/auth/logout`      | Encerra a sessão administrativa |
| GET    | `/api/auth/session`     | Verifica se existe uma sessão válida |
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
  api/auth.py                         # hash PBKDF2 e sessão HMAC em cookie HttpOnly
  api/handlers/auth_handler.py       # login, logout e status da sessão
  api/handlers/letter_segmenter_handler.py  # orquestra segmentação, comparação e histórico
  api/middleware/error_handler.py    # captura exceções não tratadas e devolve JSON 500
  core/factory/segmenter_factory.py  # cria o segmentador padrão
  core/segmenters/improved_segmenter.py  # executa pipeline dos 7 passos, desmembramento de letras, filtros e cálculo de breakdown transparente
  core/processors/opencv_processor.py    # métodos de visão computacional do PDF (bilateral, otsu, canny, contornos)
  core/validators/letter_validator.py    # validação morfológica, cálculo dos 4 pilares físicos e notas de confiança individuais
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
11. **Cálculo Transparente de Confiabilidade:** decomposição dos 4 pilares físicos (morfologia, contraste, coerência de linha e solidez) gerando o objeto auditável `confidence_breakdown` e as notas individuais por caractere;
12. **Persistência:** salvamento automático do registro no histórico quando o MongoDB estiver habilitado;
13. **Retorno estruturado:** payload com letras recortadas (com `confidenceDetails`), overlay de debug, transcript, metadados com `confidenceBreakdown`, diagnósticos em tempo real (`warnings`) e array `steps`.

### Frontend

```text
frontend/src/
  components/Segmenter/Segmenter.tsx            # tela principal: orquestra upload, comparação, histórico e abas
  components/LetterGrid/LetterGrid.tsx          # grade de letras recortadas, pílula interativa e auditoria dos 4 pilares
  components/PipelineViewer/PipelineViewer.tsx  # visualizador das 7 etapas do PDF e painel de transparência técnica
  components/ControlPanel/ControlPanel.tsx      # painel com seletor de modo e toggles de precisão
  components/ImageUploader/ImageUploader.tsx    # upload e preview da imagem original e de comparação
  components/common/                            # LoadingSpinner e ErrorMessage
  hooks/useSegmenter.ts                         # chama POST /api/segment e mantém estado reativo
  hooks/useImageUpload.ts                       # controla upload/preview de imagem em base64
  services/api.ts                               # client axios para todos os endpoints da API
frontend/public/
  manifest.webmanifest                          # metadados de instalação do PWA
  sw.js                                         # cache do shell estático em produção
  icons/                                        # ícones instaláveis em SVG (geral, 192 e 512 px)
```

A interface oferece:

- **Seletor de Modo:** alternância imediata entre *Aprimorado (PDF + Refinamentos de Precisão)* e *Acadêmico Puro (Exato do PDF UFRRJ)*;
- **Toggles de Alta Precisão:** ativar/desativar desmembramento de letras coladas e filtro de elementos não-letras;
- **Visualizador Interativo do Pipeline do PDF:** carrossel para navegar pelas 7 imagens intermediárias geradas pelo OpenCV com fórmulas e explicações pedagógicas;
- **Painel de Transparência Técnica:** explicação transparente e honesta das causas físicas de imperfeições em visão computacional clássica (kerning, iluminação irregular, caracteres desconectados como 'i'/'j', glifos 'm'/'w' e formulação matemática da confiança);
- **Painel de Transparência e Auditoria de Confiabilidade (100% Auditável):** pílula interativa que expande as barras de progresso dos 4 pilares e a fórmula matemática utilizada;
- **Inspetor Geométrico de Caracteres (Modal com Auditoria de Pilares):** visualização ampliada do glifo com métricas espaciais e notas de cada pilar individual;
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

## 21. Aplicações Práticas e Potencial de Uso Real

Embora o projeto tenha nascido como exercício acadêmico da disciplina TM438, o pipeline de segmentação e comparação desenvolvido endereça um problema tecnológico concreto: **verificar semelhança de conteúdo entre imagens de texto quando não existe um documento digital nativo para comparar.**

- **Correção e checagem de integridade acadêmica em contextos de baixo recurso.** Em muitas escolas e cursos no Brasil, trabalhos e provas ainda são entregues como fotos de páginas manuscritas ou impressas (via WhatsApp, e-mail ou formulários), sem passar por um editor de texto. Ferramentas tradicionais de detecção de plágio (Turnitin e similares) operam sobre texto digital e não resolvem esse cenário. Um pipeline como o do Pattern Checker — que segmenta caracteres diretamente da imagem e compara duas submissões — é um ponto de partida real para identificar respostas copiadas nesse tipo de fluxo.
- **Pré-processamento para digitalização de arquivos e documentos antigos.** A etapa de segmentação/recorte de caracteres é a base de qualquer pipeline de OCR. O mesmo código pode servir de pré-processamento para digitalizar acervos, formulários preenchidos à mão ou documentos históricos antes de aplicar um motor de OCR mais robusto.
- **Auditoria visual e explicabilidade.** O painel de Transparência e Honestidade Técnica — que expõe cada etapa intermediária e as causas de ruído — tem valor prático em qualquer aplicação de visão computacional usada para decisões sensíveis (ex.: acadêmicas), pois permite que um humano audite *por que* o sistema chegou a determinado resultado, em vez de tratá-lo como caixa-preta.

**Limite honesto do estágio atual:** a comparação de similaridade hoje é feita por heurística (transcrição reconstruída + contagem de letras), o que é adequado para demonstrar o conceito, mas não substitui um mecanismo de similaridade textual robusto. Para uso em produção/escala, o próximo passo natural seria integrar um motor de OCR mais maduro (ex. Tesseract fine-tuned) e comparação semântica via embeddings de texto — usando o pipeline atual de segmentação/limpeza como pré-processamento de alta qualidade. Ou seja: o projeto não é uma ferramenta de plágio pronta para produção, mas a base de visão computacional que sustentaria uma.

## 22. Observações importantes

- **Fidelidade ao Trabalho em PDF:** O projeto implementa todos os 7 passos teóricos do documento acadêmico (*Imagem Load*, *GrayScale*, *Bilateral Filter*, *Otsu*, *Canny*, *Contornos* e *Recorte matricial*), tornando o processo totalmente auditável pelo frontend.
- **Transparência e Honestidade Científica:** O painel de transparência expõe com franqueza as limitações da visão computacional tradicional (kerning estreito, sombras e caracteres desconectados) e cita a conclusão oficial do trabalho dos autores.
- **Resiliência do Histórico:** Se `MONGODB_URI` estiver vazia ou se houver perda de conexão ao cluster Atlas, o aplicativo automaticamente faz fallback para armazenamento em memória (`_local_history`), garantindo que nenhuma funcionalidade do frontend quebre ou retorne erro 500.
- **Existe um `index.py` solto na raiz:** Ele contém código legado/experimental e **não é utilizado** pelo servidor FastAPI ativo (`backend/src/server.py`).
- **Segurança de credenciais:** Para produção, mantenha a string de conexão em variável de ambiente segura e nunca comite o arquivo `.env`.

## 23. Dicas de uso

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


## Alguns comandos úteis

cd "C:\Users\Handy Claude\Desktop\processamento-de-imagens\backend"

 ## Gerar AUTH_PASSWORD_HASH

 python -c "from src.api.auth import create_password_hash; print(create_password_hash('SUA_SENHA_AQUI'))"


 ## Gerar AUTH_SECRET_KEY

 python -c "import secrets; print(secrets.token_urlsafe(32))" 
