import React, { useState } from 'react';
import { PipelineStep } from '../../types';
import './PipelineViewer.css';

interface PipelineViewerProps {
  steps?: PipelineStep[];
  warnings?: string[];
  splitsCount?: number;
  filteredCount?: number;
  mode?: string;
}

export const PipelineViewer: React.FC<PipelineViewerProps> = ({
  steps = [],
  warnings = [],
  splitsCount = 0,
  filteredCount = 0,
  mode = 'enhanced',
}) => {
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<'steps' | 'transparency'>('steps');

  const currentStep = steps[activeStepIndex] || steps[0];

  return (
    <div className="pipeline-viewer-card">
      <div className="pipeline-viewer-nav">
        <div className="pipeline-nav-tabs">
          <button
            type="button"
            className={`pipeline-tab-btn ${activeTab === 'steps' ? 'active' : ''}`}
            onClick={() => setActiveTab('steps')}
          >
            🔬 Pipeline do Trabalho Acadêmico (PDF UFRRJ)
            {steps.length > 0 && <span className="tab-badge">{steps.length} etapas</span>}
          </button>
          <button
            type="button"
            className={`pipeline-tab-btn ${activeTab === 'transparency' ? 'active' : ''}`}
            onClick={() => setActiveTab('transparency')}
          >
            💡 Transparência & Limitações Técnicas
            <span className="tab-badge-highlight">Honestidade do Método</span>
          </button>
        </div>

        <div className="pipeline-mode-indicator">
          <span className="mode-tag">
            Modo atual: <strong>{mode === 'academic' ? 'PDF Puro (Acadêmico)' : 'Aprimorado (PDF + IA de Precisão)'}</strong>
          </span>
        </div>
      </div>

      {activeTab === 'steps' ? (
        <div className="pipeline-steps-content">
          {steps.length === 0 ? (
            <div className="pipeline-empty">
              <p>Processe uma imagem para visualizar todas as 7 etapas intermediárias definidas no trabalho em PDF.</p>
            </div>
          ) : (
            <>
              <div className="pipeline-stepper-strip">
                {steps.map((step, idx) => (
                  <button
                    key={step.step}
                    type="button"
                    className={`step-bubble-btn ${idx === activeStepIndex ? 'selected' : ''}`}
                    onClick={() => setActiveStepIndex(idx)}
                    title={step.title}
                  >
                    <span className="bubble-num">{step.step}</span>
                    <span className="bubble-label">{step.title.split(':')[1] || step.title}</span>
                  </button>
                ))}
              </div>

              {currentStep && (
                <div className="step-detail-card">
                  <div className="step-header">
                    <div>
                      <span className="step-tag">Etapa {currentStep.step} de {steps.length}</span>
                      <h3 className="step-title">{currentStep.title}</h3>
                    </div>
                    <div className="step-technique-pill">
                      <code>{currentStep.technique}</code>
                    </div>
                  </div>

                  <div className="step-visual-body">
                    <div className="step-image-box">
                      <img
                        src={currentStep.image}
                        alt={currentStep.title}
                        className="step-preview-img"
                      />
                    </div>

                    <div className="step-info-box">
                      {currentStep.formula && (
                        <div className="formula-box">
                          <span className="formula-label">Fórmula / Método Matemático:</span>
                          <code className="formula-code">{currentStep.formula}</code>
                        </div>
                      )}

                      <div className="step-description-text">
                        <h4>Fundamentação Técnica do Trabalho:</h4>
                        <p>{currentStep.description}</p>
                      </div>

                      <div className="step-controls">
                        <button
                          type="button"
                          className="btn-step-nav"
                          disabled={activeStepIndex === 0}
                          onClick={() => setActiveStepIndex((prev) => Math.max(0, prev - 1))}
                        >
                          ← Etapa Anterior
                        </button>
                        <span className="step-counter">
                          {activeStepIndex + 1} / {steps.length}
                        </span>
                        <button
                          type="button"
                          className="btn-step-nav"
                          disabled={activeStepIndex === steps.length - 1}
                          onClick={() => setActiveStepIndex((prev) => Math.min(steps.length - 1, prev + 1))}
                        >
                          Próxima Etapa →
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="transparency-content">
          <div className="transparency-intro">
            <h3>Transparência sobre Detecção, Ruídos e Limites do Processamento</h3>
            <p>
              Para que a aplicação seja 100% transparente e com objetivo honesto, esta seção detalha os princípios
              físicos e matemáticos que influenciam a precisão da detecção e como o algoritmo lida com as imperfeições da visão computacional tradicional.
            </p>
          </div>

          <div className="transparency-grid">
            <div className="transparency-card">
              <div className="transparency-card-icon">🔤</div>
              <h4>1. Por que letras podem ser agrupadas? (Kerning & Ligaduras)</h4>
              <p>
                Em fontes condensadas, itálicas ou manuscritas, a distância horizontal entre dois caracteres adjacentes pode ser de apenas 1 ou 2 pixels.
                Durante a binarização de Otsu e o filtro Canny, esses pixels de contato formam um único contorno contínuo, fazendo com que o retângulo envolvente (<code>boundingRect</code>) abrace mais de uma letra.
              </p>
              <div className="transparency-solution">
                <strong>Solução implementada:</strong> Aplicamos análise do <em>Perfil de Projeção Vertical</em> para mapear a densidade de tinta ao longo de cada coluna e localizar os <em>vales locais</em> onde as letras se tocam, cortando e recalculando as caixas individuais.
                {splitsCount > 0 && <span className="stat-pill">{splitsCount} letras agrupadas foram separadas nesta imagem!</span>}
              </div>
            </div>

            <div className="transparency-card">
              <div className="transparency-card-icon">🧹</div>
              <h4>2. Por que elementos que não são letras são recortados?</h4>
              <p>
                O algoritmo original do trabalho busca contornos fechados (<code>cv2.findContours</code>) e gera um Bounding Box para cada um.
                Linhas horizontais (sublinhados), linhas verticais (molduras, margens da folha), ilustrações ou manchas de sujeira possuem intensidade escura similar à tinta e geram contornos válidos para o OpenCV.
              </p>
              <div className="transparency-solution">
                <strong>Solução implementada:</strong> Adicionamos filtros morfológicos refinados que analisam a razão de aspecto (largura/altura), a solidez geométrica (eliminando blocos 100% sólidos) e a densidade de contorno para descartar linhas e ruídos decorativos.
                {filteredCount > 0 && <span className="stat-pill">{filteredCount} elementos não-letra descartados nesta imagem!</span>}
              </div>
            </div>

            <div className="transparency-card">
              <div className="transparency-card-icon">🌗</div>
              <h4>3. Variação de Iluminação e Sombras</h4>
              <p>
                O Método de Otsu assume uma distribuição bimodal global de intensidades (fundo claro e texto escuro).
                Se uma foto apresentar iluminação desigual (por exemplo, sombra de celular ou reflexo de flash), o limiar global pode binarizar incorretamente partes da imagem, gerando ruído de sal-e-pimenta ou caracteres com traços rompidos.
              </p>
              <div className="transparency-solution">
                <strong>Mitigação:</strong> A aplicação utiliza o <em>Filtro Bilateral</em> ($d=10, \sigma=75$) conforme recomendado no trabalho para suavizar gradientes preservando bordas vivas, além de equalização adaptativa (CLAHE) no modo aprimorado.
              </div>
            </div>

            <div className="transparency-card">
              <div className="transparency-card-icon">📍</div>
              <h4>4. Caracteres Desconectados (Pingos e Acentos)</h4>
              <p>
                Caracteres como as letras minúsculas <code>i</code> e <code>j</code>, pontuações (<code>:</code>, <code>;</code>, <code>?</code>, <code>!</code>) e letras acentuadas (<code>á</code>, <code>ç</code>, <code>õ</code>) são formados fisicamente por dois ou mais contornos desconectados.
                Na visão clássica, o pingo e a haste são detectados inicialmente como componentes separados.
              </p>
              <div className="transparency-solution">
                <strong>Mitigação:</strong> O agrupador por linha organiza os fragmentos na mesma linha de leitura, preservando a coerência espacial do texto.
              </div>
            </div>
          </div>

          <div className="academic-quote-box">
            <span className="quote-icon">📜</span>
            <div className="quote-text">
              <strong>Citação Oficial do Documento Acadêmico (UFRRJ - TM438):</strong>
              <em>
                "O algoritmo funciona para todas as imagens que estão na pasta, mas é mais eficiente no caso das imagens que são compostas por palavras ou letras maiores."
              </em>
              <span className="quote-author">— Trabalho de Processamento de Imagens, Handy Claude Milliance & Deived William (Prof. Bruno Dembogurski).</span>
            </div>
          </div>

          {warnings.length > 0 && (
            <div className="transparency-warnings">
              <h4>Diagnósticos em Tempo Real da Imagem Atual:</h4>
              <ul>
                {warnings.map((w, index) => (
                  <li key={index}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
