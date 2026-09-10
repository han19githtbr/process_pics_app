// frontend/src/components/ImageEnhancer/ImageEnhancer.tsx
import React, { useState } from 'react';
import {
  Sparkles,
  LogOut,
  Wand2,
  ChevronLeft,
  ChevronRight,
  Code2,
  Gauge,
  Focus,
  Activity,
  Contrast,
  Database,
  CheckCircle2,
} from 'lucide-react';
import { ImageUploader } from '../ImageUploader';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { ImageBank } from '../ImageBank';
import { EnhanceResult } from '../../types';
import { enhanceImage } from '../../services/api';
import './ImageEnhancer.css';

type ImageEnhancerProps = {
  onLogout?: () => void;
};

export const ImageEnhancer: React.FC<ImageEnhancerProps> = ({ onLogout }) => {
  const [image, setImage] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EnhanceResult | null>(null);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [compareView, setCompareView] = useState<'depois' | 'antes'>('depois');
  const [loggingOut, setLoggingOut] = useState(false);
  const [bankRefreshSignal, setBankRefreshSignal] = useState(0);

  const handleUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      setImage(reader.result as string);
      setFileName(file.name);
      setResult(null);
      setError(null);
      setActiveStepIndex(0);
      setCompareView('depois');
    };
    reader.readAsDataURL(file);
  };

  const handleReset = () => {
    setImage(null);
    setFileName(undefined);
    setResult(null);
    setError(null);
  };

  const handleEnhance = async () => {
    if (!image) return;
    setLoading(true);
    setError(null);
    try {
      const data = await enhanceImage(image, { mode: 'auto' }, fileName, false);
      setResult(data);
      setActiveStepIndex(0);
      setCompareView('depois');
      if (data.savedToBank) {
        setBankRefreshSignal((n) => n + 1);
      }
    } catch (err: any) {
      const backendMessage = err?.response?.data?.error;
      setError(
        backendMessage ||
          'Não foi possível melhorar a qualidade da imagem. Verifique a conexão com o backend.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (!onLogout || loggingOut) return;
    if (!window.confirm('Deseja encerrar a sessão e voltar para a tela de login?')) return;

    setLoggingOut(true);
    try {
      await onLogout();
    } finally {
      setLoggingOut(false);
    }
  };

  const currentStep = result?.steps?.[activeStepIndex];
  const metrics = result?.metrics;

  return (
    <div className="segmenter-container">
      {/* Reaproveita o cabeçalho visual do módulo de Segmentação (Segmenter.css) */}
      <header className="segmenter-header">
        <div className="segmenter-header-row">
          <div className="brand-identity">
            <div className="brand-logo-box">
              <Sparkles size={22} className="brand-logo-icon" />
            </div>
            <div>
              <div className="brand-title-wrap">
                <h1>Melhoria de Qualidade</h1>
                <span className="brand-badge">Banco de Alta Qualidade</span>
              </div>
              <p>Restauração científica de imagens de texto de baixa qualidade, com transparência total sobre a técnica usada</p>
            </div>
          </div>

          <div className="header-actions">
            <div className="backend-status-pill">
              <span className="status-live-dot" />
              <span>Sistema Pronto</span>
            </div>

            {onLogout && (
              <button
                type="button"
                className="logout-btn"
                onClick={() => void handleLogout()}
                disabled={loggingOut}
                aria-label="Sair da conta"
                title="Encerrar sessão e voltar para a tela de login"
              >
                <LogOut size={16} />
                <span className="logout-label">{loggingOut ? 'Saindo...' : 'Sair'}</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="segmenter-content">
        <main className="main-content enhancer-main-content">
          <div className="upload-card">
            <div className="upload-card-header">
              <div className="card-header-label">
                <span className={`status-dot ${image ? 'active' : ''}`} />
                <span>Imagem de Baixa Qualidade</span>
              </div>
              {image && <span className="card-badge-ready">Carregada</span>}
            </div>
            <ImageUploader
              onImageUpload={handleUpload}
              image={image}
              onReset={handleReset}
              fileName={fileName}
            />
          </div>

          <div className="enhancer-actions">
            <button
              type="button"
              className="btn btn-compare enhancer-btn-run"
              onClick={() => void handleEnhance()}
              disabled={loading || !image}
            >
              <Wand2 size={17} />
              <span>{loading ? 'Restaurando Qualidade...' : 'Melhorar Qualidade da Imagem'}</span>
            </button>
            <p className="enhancer-hint">
              A imagem melhorada é salva automaticamente no <strong>Banco de Imagens de Alta Qualidade</strong>, logo abaixo.
            </p>
          </div>

          {loading && (
            <LoadingSpinner
              label="Restaurando Qualidade da Imagem..."
              subtext="Escala adaptativa, redução de ruído, balanço de branco, CLAHE e nitidez em andamento"
            />
          )}

          {error && <ErrorMessage message={error} title="Falha na melhoria de qualidade" />}

          {result && (
            <>
              {result.savedToBank && (
                <div className="enhancer-saved-banner">
                  <CheckCircle2 size={16} />
                  <span>Imagem melhorada salva no Banco de Imagens de Alta Qualidade.</span>
                </div>
              )}

              {/* Comparação Antes / Depois */}
              <section className="enhancer-compare-card" aria-label="Comparação antes e depois">
                <div className="enhancer-compare-toggle">
                  <button
                    type="button"
                    className={`toggle-tab-btn ${compareView === 'antes' ? 'active' : ''}`}
                    onClick={() => setCompareView('antes')}
                  >
                    Antes
                  </button>
                  <button
                    type="button"
                    className={`toggle-tab-btn ${compareView === 'depois' ? 'active' : ''}`}
                    onClick={() => setCompareView('depois')}
                  >
                    Depois
                  </button>
                </div>
                <div className="enhancer-compare-viewport">
                  <img
                    src={compareView === 'depois' ? result.enhancedImage : result.originalImage}
                    alt={compareView === 'depois' ? 'Imagem melhorada' : 'Imagem original'}
                    className="enhancer-compare-image"
                  />
                </div>
              </section>

              {/* Métricas de qualidade Antes/Depois */}
              {metrics && (
                <div className="comparison-metrics enhancer-metrics-grid">
                  <div className="metric-card">
                    <div className="metric-icon-wrap">
                      <Focus size={16} />
                    </div>
                    <div className="metric-data">
                      <span>Nitidez (Var. Laplaciano)</span>
                      <strong>{metrics.sharpnessBefore?.toFixed(1)} → {metrics.sharpnessAfter?.toFixed(1)}</strong>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon-wrap">
                      <Activity size={16} />
                    </div>
                    <div className="metric-data">
                      <span>Ruído (Resíduo Mediana)</span>
                      <strong>{metrics.noiseBefore?.toFixed(1)} → {metrics.noiseAfter?.toFixed(1)}</strong>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon-wrap">
                      <Contrast size={16} />
                    </div>
                    <div className="metric-data">
                      <span>Contraste (Desvio Padrão)</span>
                      <strong>{metrics.contrastBefore?.toFixed(1)} → {metrics.contrastAfter?.toFixed(1)}</strong>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon-wrap">
                      <Gauge size={16} />
                    </div>
                    <div className="metric-data">
                      <span>Tempo de Processamento</span>
                      <strong>{metrics.processingTime?.toFixed(2)}s</strong>
                    </div>
                  </div>
                </div>
              )}
              {metrics?.comparisonNote && (
                <p className="enhancer-comparison-note">{metrics.comparisonNote}</p>
              )}

              {/* Pipeline de técnicas aplicadas */}
              {result.steps && result.steps.length > 0 && currentStep && (
                <div className="pipeline-viewer-card enhancer-steps-card">
                  <div className="pipeline-viewer-nav">
                    <div className="pipeline-nav-tabs">
                      <button type="button" className="pipeline-tab-btn active">
                        <Sparkles size={16} />
                        <span>Técnica Científica Aplicada</span>
                        <span className="tab-badge">{result.steps.length} etapas</span>
                      </button>
                    </div>
                  </div>

                  <div className="pipeline-steps-content">
                    <div className="pipeline-stepper-strip">
                      {result.steps.map((step, idx) => (
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

                    <div className="step-detail-card">
                      <div className="step-header">
                        <div>
                          <span className="step-tag">Etapa {currentStep.step} de {result.steps.length}</span>
                          <h3 className="step-title">{currentStep.title}</h3>
                        </div>
                        <div className="step-technique-pill">
                          <Code2 size={13} />
                          <code>{currentStep.technique}</code>
                        </div>
                      </div>

                      <div className="step-visual-body">
                        <div className="step-image-box">
                          <img src={currentStep.image} alt={currentStep.title} className="step-preview-img" />
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
                              {activeStepIndex + 1} / {result.steps.length}
                            </span>
                            <button
                              type="button"
                              className="btn-step-nav"
                              disabled={activeStepIndex === result.steps.length - 1}
                              onClick={() => setActiveStepIndex((prev) => Math.min((result.steps?.length ?? 1) - 1, prev + 1))}
                            >
                              <span>Próxima</span>
                              <ChevronRight size={15} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Banco de Imagens de Alta Qualidade */}
          <div className="enhancer-bank-section">
            <div className="enhancer-bank-title">
              <Database size={17} />
              <h3>Banco de Imagens de Alta Qualidade</h3>
            </div>
            <ImageBank refreshSignal={bankRefreshSignal} />
          </div>
        </main>
      </div>
    </div>
  );
};
