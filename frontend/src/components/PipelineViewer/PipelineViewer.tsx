import React, { useState } from 'react';
import {
  Microscope,
  Lightbulb,
  Cpu,
  ChevronLeft,
  ChevronRight,
  Split,
  Filter,
  SunMedium,
  Compass,
  Quote,
  AlertTriangle,
  Code2,
} from 'lucide-react';
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
            <Microscope size={16} />
            <span>Pipeline de Processamento</span>
            {steps.length > 0 && <span className="tab-badge">{steps.length} etapas</span>}
          </button>
          <button
            type="button"
            className={`pipeline-tab-btn ${activeTab === 'transparency' ? 'active' : ''}`}
            onClick={() => setActiveTab('transparency')}
          >
            <Lightbulb size={16} />
            <span>Fundamentação & Limitações</span>
            <span className="tab-badge-highlight">Transparência Técnica</span>
          </button>
        </div>

        <div className="pipeline-mode-indicator">
          <Cpu size={14} className="mode-tag-icon" />
          <span className="mode-tag">
            Modo: <strong>{mode === 'academic' ? 'Literatura Acadêmica P.I.' : 'Aprimorado (Visão Computacional)'}</strong>
          </span>
        </div>
      </div>

      {activeTab === 'steps' ? (
        <div className="pipeline-steps-content">
          {steps.length === 0 ? (
            <div className="pipeline-empty">
              <div className="empty-icon-box">
                <Microscope size={26} />
              </div>
              <h4>Pipeline aguardando processamento</h4>
              <p>Execute a segmentação de uma imagem para inspecionar visualmente cada uma das 7 etapas de transformações matriciais.</p>
            </div>
          ) : (
            <>
              {/* Stepper Strip */}
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

              {/* Step Detail Card */}
              {currentStep && (
                <div className="step-detail-card">
                  <div className="step-header">
                    <div>
                      <span className="step-tag">Etapa {currentStep.step} de {steps.length}</span>
                      <h3 className="step-title">{currentStep.title}</h3>
                    </div>
                    <div className="step-technique-pill">
                      <Code2 size={13} />
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
                          <span className="formula-label">Fórmula / Operador Matemático:</span>
                          <code className="formula-code">{currentStep.formula}</code>
                        </div>
                      )}

                      <div className="step-description-text">
                        <h4>Fundamentação Técnica do Operador:</h4>
                        <p>{currentStep.description}</p>
                      </div>

                      <div className="step-controls">
                        <button
                          type="button"
                          className="btn-step-nav"
                          disabled={activeStepIndex === 0}
                          onClick={() => setActiveStepIndex((prev) => Math.max(0, prev - 1))}
                        >
                          <ChevronLeft size={15} />
                          <span>Anterior</span>
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
                          <span>Próxima</span>
                          <ChevronRight size={15} />
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
        /* Transparency & Technical Limitations */
        <div className="transparency-content">
          <div className="transparency-intro">
            <h3>Transparência sobre Detecção, Ruídos e Limitações do Método</h3>
            <p>
              Em conformidade com as boas práticas científicas, esta seção detalha os princípios
              físicos e matemáticos que influenciam a precisão dos operadores e como o sistema resolve as imperfeições clássicas da visão computacional.
            </p>
          </div>

          <div className="transparency-grid">
            <div className="transparency-card">
              <div className="transparency-card-icon-box">
                <Split size={20} />
              </div>
              <h4>1. Por que letras podem ser agrupadas? (Kerning & Ligaduras)</h4>
              <p>
                Em fontes condensadas, itálicas ou manuscritas, a distância horizontal entre dois caracteres adjacentes pode ser de apenas 1 ou 2 pixels.
                Durante a binarização de Otsu e o filtro Canny, esses pixels de contato formam um único contorno contínuo, fazendo com que o retângulo envolvente (<code>boundingRect</code>) abrace mais de uma letra.
              </p>
              <div className="transparency-solution">
                <strong>Solução implementada:</strong> Análise do <em>Perfil de Projeção Vertical</em> para mapear a densidade de tinta ao longo de cada coluna e localizar os <em>vales locais</em> onde as letras se tocam, dividindo as caixas individuais.
                {splitsCount > 0 && <span className="stat-pill">{splitsCount} letras agrupadas foram separadas nesta imagem!</span>}
              </div>
            </div>

            <div className="transparency-card">
              <div className="transparency-card-icon-box">
                <Filter size={20} />
              </div>
              <h4>2. Por que elementos não-texto podem ser recortados?</h4>
              <p>
                O algoritmo original busca contornos fechados (<code>cv2.findContours</code>) e gera uma bounding box para cada um.
                Linhas horizontais (sublinhados), molduras de folha, manchas ou logos possuem intensidade escura similar à tinta e geram contornos válidos para o OpenCV.
              </p>
              <div className="transparency-solution">
                <strong>Solução implementada:</strong> Filtros morfológicos refinados que analisam a razão de aspecto (largura/altura), solidez geométrica e densidade de contorno para descartar linhas e ruídos decorativos.
                {filteredCount > 0 && <span className="stat-pill">{filteredCount} elementos não-letra descartados nesta imagem!</span>}
              </div>
            </div>

            <div className="transparency-card">
              <div className="transparency-card-icon-box">
                <SunMedium size={20} />
              </div>
              <h4>3. Variação de Iluminação e Sombras</h4>
              <p>
                O Método de Otsu assume uma distribuição bimodal global de intensidades (fundo claro e texto escuro).
                Se uma foto apresentar iluminação desigual (por exemplo, sombra de celular ou reflexo de flash), o limiar global pode binarizar incorretamente partes da imagem, gerando ruído de sal-e-pimenta.
              </p>
              <div className="transparency-solution">
                <strong>Mitigação:</strong> Utilização do <em>Filtro Bilateral</em> ($d=10, \sigma=75$) conforme recomendado no trabalho para suavizar gradientes preservando bordas vivas, além de equalização adaptativa (CLAHE).
              </div>
            </div>

            <div className="transparency-card">
              <div className="transparency-card-icon-box">
                <Compass size={20} />
              </div>
              <h4>4. Caracteres Desconectados (Pingos e Acentos)</h4>
              <p>
                Caracteres como as letras minúsculas <code>i</code> e <code>j</code>, pontuações (<code>:</code>, <code>;</code>, <code>?</code>, <code>!</code>) e letras acentuadas (<code>á</code>, <code>ç</code>, <code>õ</code>) são formados fisicamente por dois ou mais contornos desconectados.
              </p>
              <div className="transparency-solution">
                <strong>Mitigação:</strong> O agrupador por linha organiza os fragmentos na mesma linha de leitura, preservando a coerência espacial do texto.
              </div>
            </div>
          </div>

          <div className="academic-quote-box">
            <Quote size={24} className="quote-icon" />
            <div className="quote-text">
              <span className="quote-badge">Citação Oficial da Literatura de Referência</span>
              <em>
                "O algoritmo funciona para todas as imagens que estão na pasta, mas é mais eficiente no caso das imagens que são compostas por palavras ou letras maiores."
              </em>
              <span className="quote-author">— Sistema de Processamento de Imagens e Visão Computacional.</span>
            </div>
          </div>

          {warnings.length > 0 && (
            <div className="transparency-warnings">
              <div className="warnings-header">
                <AlertTriangle size={18} />
                <h4>Diagnósticos em Tempo Real da Imagem Atual:</h4>
              </div>
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

