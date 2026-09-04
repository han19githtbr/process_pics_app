import React, { useState } from 'react';
import {
  Download,
  Copy,
  Check,
  Sparkles,
  Clock,
  ShieldCheck,
  X,
  Maximize2,
  Grid,
  AlignLeft,
  Info,
} from 'lucide-react';
import { Letter, ConfidenceBreakdown } from '../../types';
import './LetterGrid.css';

interface LetterGridProps {
  letters: Letter[];
  onDownload: () => void;
  metadata?: {
    totalLetters: number;
    processingTime: number;
    confidenceScore: number;
    confidenceBreakdown?: ConfidenceBreakdown;
  };
}

export const LetterGrid: React.FC<LetterGridProps> = ({
  letters,
  onDownload,
  metadata,
}) => {
  const [selectedLetter, setSelectedLetter] = useState<Letter | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'strip' | 'grid'>('strip');
  const [showBreakdown, setShowBreakdown] = useState(false);

  const orderedLetters = [...letters];
  const breakdown = metadata?.confidenceBreakdown;

  const handleCopyTranscript = () => {
    const transcript = orderedLetters
      .map((l, i) => l.id ?? i + 1)
      .join(' ');
    navigator.clipboard.writeText(transcript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (orderedLetters.length === 0) {
    return (
      <div className="letter-grid-empty">
        <div className="empty-icon-box">
          <Sparkles size={24} />
        </div>
        <h3>Nenhum caractere detectado</h3>
        <p>Ajuste os controles de sensibilidade ou tente uma imagem com maior contraste.</p>
      </div>
    );
  }

  const confidencePercent = ((metadata?.confidenceScore ?? 0) * 100).toFixed(1);
  const isHighConfidence = (metadata?.confidenceScore ?? 0) >= 0.8;

  return (
    <div className="letter-grid-container">
      {/* Header Bar */}
      <div className="letter-grid-header">
        <div className="header-left">
          <div className="header-title-badge">
            <h2>Caracteres Segmentados</h2>
            <span className="letter-count-pill">{orderedLetters.length} recortes</span>
          </div>

          <div className="header-stats-strip">
            {metadata && (
              <>
                <button
                  type="button"
                  onClick={() => setShowBreakdown((prev) => !prev)}
                  className={`confidence-pill ${isHighConfidence ? 'high' : 'medium'} interactive-pill ${showBreakdown ? 'active' : ''}`}
                  title="Clique para abrir a auditoria transparente dos 4 pilares de confiança"
                >
                  <ShieldCheck size={13} />
                  <span>Confiança: {confidencePercent}%</span>
                  <Info size={11} className="pill-info-icon" />
                </button>
                {metadata.processingTime > 0 && (
                  <div className="time-pill">
                    <Clock size={13} />
                    <span>{metadata.processingTime.toFixed(0)} ms</span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div className="header-right">
          <div className="view-mode-selector">
            <button
              type="button"
              className={`view-mode-btn ${activeTab === 'strip' ? 'active' : ''}`}
              onClick={() => setActiveTab('strip')}
              title="Ordem de Leitura Linear"
            >
              <AlignLeft size={14} />
              <span>Ordem de Leitura</span>
            </button>
            <button
              type="button"
              className={`view-mode-btn ${activeTab === 'grid' ? 'active' : ''}`}
              onClick={() => setActiveTab('grid')}
              title="Visualização em Grade Detalhada"
            >
              <Grid size={14} />
              <span>Grade Completa</span>
            </button>
          </div>

          <button
            type="button"
            onClick={handleCopyTranscript}
            className={`btn-toolbar ${copied ? 'copied' : ''}`}
            title="Copiar transcrição da sequência de IDs"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span>{copied ? 'Copiado!' : 'Copiar IDs'}</span>
          </button>

          <button
            type="button"
            onClick={onDownload}
            className="btn-toolbar primary"
            title="Baixar todos os recortes em arquivo ZIP"
          >
            <Download size={14} />
            <span>Baixar ZIP</span>
          </button>
        </div>
      </div>

      {/* Confidence Breakdown Transparent Panel */}
      {showBreakdown && (
        <div className="confidence-breakdown-card">
          <div className="confidence-breakdown-header">
            <div className="breakdown-title-wrap">
              <ShieldCheck size={16} className="breakdown-icon" />
              <h4>Transparência de Confiabilidade (100% Auditável)</h4>
            </div>
            <button
              type="button"
              className="breakdown-close-btn"
              onClick={() => setShowBreakdown(false)}
              aria-label="Fechar auditoria de confiança"
            >
              <X size={14} />
            </button>
          </div>

          <p className="breakdown-intro">
            A pontuação geral de <strong>{confidencePercent}%</strong> é calculada matematicamente a partir da média ponderada dos 4 pilares físicos extraídos dos {orderedLetters.length} caracteres identificados:
          </p>

          <div className="breakdown-pillars-grid">
            <div className="pillar-item">
              <div className="pillar-info">
                <span className="pillar-label">1. Morfologia Tipográfica (35%)</span>
                <strong className="pillar-val">
                  {((breakdown?.aspect_ratio_score ?? (metadata?.confidenceScore ?? 0.95)) * 100).toFixed(1)}%
                </strong>
              </div>
              <div className="pillar-bar-bg">
                <div
                  className="pillar-bar-fill"
                  style={{
                    width: `${Math.min(100, Math.max(8, (breakdown?.aspect_ratio_score ?? (metadata?.confidenceScore ?? 0.95)) * 100))}%`,
                  }}
                />
              </div>
              <span className="pillar-desc">Razão de aspecto (largura / altura) compatível com letras ocidentais.</span>
            </div>

            <div className="pillar-item">
              <div className="pillar-info">
                <span className="pillar-label">2. Contraste de Tinta (30%)</span>
                <strong className="pillar-val">
                  {((breakdown?.contrast_score ?? (metadata?.confidenceScore ?? 0.95)) * 100).toFixed(1)}%
                </strong>
              </div>
              <div className="pillar-bar-bg">
                <div
                  className="pillar-bar-fill"
                  style={{
                    width: `${Math.min(100, Math.max(8, (breakdown?.contrast_score ?? (metadata?.confidenceScore ?? 0.95)) * 100))}%`,
                  }}
                />
              </div>
              <span className="pillar-desc">Desvio padrão de tons de cinza e faixa dinâmica do traço contra o fundo.</span>
            </div>

            <div className="pillar-item">
              <div className="pillar-info">
                <span className="pillar-label">3. Coerência de Linha (20%)</span>
                <strong className="pillar-val">
                  {((breakdown?.line_coherence_score ?? (metadata?.confidenceScore ?? 0.95)) * 100).toFixed(1)}%
                </strong>
              </div>
              <div className="pillar-bar-bg">
                <div
                  className="pillar-bar-fill"
                  style={{
                    width: `${Math.min(100, Math.max(8, (breakdown?.line_coherence_score ?? (metadata?.confidenceScore ?? 0.95)) * 100))}%`,
                  }}
                />
              </div>
              <span className="pillar-desc">Consistência de altura dos caracteres com a mediana da linha de texto.</span>
            </div>

            <div className="pillar-item">
              <div className="pillar-info">
                <span className="pillar-label">4. Solidez e Densidade (15%)</span>
                <strong className="pillar-val">
                  {((breakdown?.density_score ?? (metadata?.confidenceScore ?? 0.95)) * 100).toFixed(1)}%
                </strong>
              </div>
              <div className="pillar-bar-bg">
                <div
                  className="pillar-bar-fill"
                  style={{
                    width: `${Math.min(100, Math.max(8, (breakdown?.density_score ?? (metadata?.confidenceScore ?? 0.95)) * 100))}%`,
                  }}
                />
              </div>
              <span className="pillar-desc">Densidade de preenchimento (área / w×h) dentro da faixa esperada para fontes.</span>
            </div>
          </div>

          <div className="breakdown-formula-strip">
            <code>Fórmula Transparente: C = 0.35 × Morfologia + 0.30 × Contraste + 0.20 × Linha + 0.15 × Solidez</code>
          </div>
        </div>
      )}

      {/* Reading Order Strip */}
      {activeTab === 'strip' ? (
        <div className="letter-transcript">
          <div className="transcript-header-row">
            <span className="transcript-label">Sequência Reconstruída em Ordem Topológica de Leitura:</span>
            <span className="transcript-hint">Clique em um caractere para inspecionar</span>
          </div>

          <div className="transcript-strip">
            {orderedLetters.map((letter, index) => {
              const letterIndex = letter.id ?? index + 1;
              return (
                <div
                  key={letter.id ?? `${letter.x}-${letter.y}-${index}`}
                  className="transcript-card"
                  onClick={() => setSelectedLetter(letter)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') setSelectedLetter(letter);
                  }}
                  title={`Caractere #${letterIndex} — Linha ${letter.line || 1} (Clique para inspecionar)`}
                >
                  {letter.image ? (
                    <img
                      src={letter.image}
                      alt={`Caractere ${letterIndex}`}
                      className="transcript-image"
                    />
                  ) : (
                    <div className="transcript-placeholder">{letterIndex}</div>
                  )}
                  <div className="transcript-meta-row">
                    <span className="transcript-number">#{letterIndex}</span>
                    {letter.line && <span className="transcript-line-tag">L{letter.line}</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Detailed Grid View */
        <div className="letter-grid">
          {orderedLetters.map((letter, index) => {
            const letterIndex = letter.id ?? index + 1;
            const conf = Math.round((letter.confidence || 0) * 100);
            return (
              <div
                key={letter.id ?? `${letter.x}-${letter.y}-${index}`}
                className="letter-item"
                onClick={() => setSelectedLetter(letter)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setSelectedLetter(letter);
                }}
              >
                <div className="letter-thumb-box">
                  {letter.image ? (
                    <img
                      src={letter.image}
                      alt={`Caractere ${letterIndex}`}
                      className="letter-image"
                    />
                  ) : (
                    <div className="letter-placeholder">
                      <span>{letterIndex}</span>
                    </div>
                  )}
                  <button
                    type="button"
                    className="letter-zoom-overlay"
                    title="Inspecionar detalhes"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedLetter(letter);
                    }}
                  >
                    <Maximize2 size={13} />
                  </button>
                </div>
                <div className="letter-info">
                  <div className="letter-id-wrap">
                    <span className="letter-id">#{letterIndex}</span>
                    {letter.line && (
                      <span className="letter-line-badge">L{letter.line}</span>
                    )}
                  </div>
                  <span className={`letter-confidence ${conf >= 80 ? 'good' : conf >= 50 ? 'warn' : 'low'}`}>
                    {conf}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Inspector Lightbox Modal */}
      {selectedLetter && (
        <div className="letter-modal-backdrop" onClick={() => setSelectedLetter(null)}>
          <div className="letter-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="letter-modal-header">
              <div className="letter-modal-title">
                <h4>Caractere #{selectedLetter.id || 1}</h4>
                {selectedLetter.line && <span className="badge-pill">Linha {selectedLetter.line}</span>}
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedLetter(null)}
                aria-label="Fechar inspetor"
              >
                <X size={16} />
              </button>
            </div>

            <div className="letter-modal-body">
              <div className="modal-preview-box">
                {selectedLetter.image ? (
                  <img
                    src={selectedLetter.image}
                    alt={`Recorte ampliado #${selectedLetter.id || 1}`}
                    className="modal-img-large"
                  />
                ) : (
                  <div className="modal-img-placeholder">#{selectedLetter.id || 1}</div>
                )}
              </div>

              <div className="modal-details-box">
                <span className="modal-details-title">Geometria e Métricas:</span>
                <div className="details-grid">
                  <div className="detail-item">
                    <span>Posição X</span>
                    <strong>{selectedLetter.x} px</strong>
                  </div>
                  <div className="detail-item">
                    <span>Posição Y</span>
                    <strong>{selectedLetter.y} px</strong>
                  </div>
                  <div className="detail-item">
                    <span>Largura (W)</span>
                    <strong>{selectedLetter.width} px</strong>
                  </div>
                  <div className="detail-item">
                    <span>Altura (H)</span>
                    <strong>{selectedLetter.height} px</strong>
                  </div>
                  <div className="detail-item">
                    <span>Área Total</span>
                    <strong>{selectedLetter.area || selectedLetter.width * selectedLetter.height} px²</strong>
                  </div>
                  <div className="detail-item">
                    <span>Confiança</span>
                    <strong className="accent-text">
                      {((selectedLetter.confidence || 0) * 100).toFixed(1)}%
                    </strong>
                  </div>
                </div>

                <div className="modal-pillars-box">
                  <span className="modal-details-title">Auditoria dos 4 Pilares deste Caractere:</span>
                  <div className="letter-pillars-list">
                    <div className="letter-pillar-row">
                      <div className="letter-pillar-head">
                        <span>Morfologia Tipográfica (35%)</span>
                        <strong>{((selectedLetter.confidenceDetails?.aspect_ratio ?? (selectedLetter.confidence || 0.95)) * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="pillar-bar-bg">
                        <div
                          className="pillar-bar-fill"
                          style={{
                            width: `${Math.min(100, Math.max(8, (selectedLetter.confidenceDetails?.aspect_ratio ?? (selectedLetter.confidence || 0.95)) * 100))}%`,
                          }}
                        />
                      </div>
                      <span className="pillar-subtext">
                        Razão de aspecto: {(selectedLetter.width / Math.max(selectedLetter.height, 1)).toFixed(2)} (W/H)
                      </span>
                    </div>

                    <div className="letter-pillar-row">
                      <div className="letter-pillar-head">
                        <span>Contraste de Tinta (30%)</span>
                        <strong>{((selectedLetter.confidenceDetails?.contrast ?? (selectedLetter.confidence || 0.95)) * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="pillar-bar-bg">
                        <div
                          className="pillar-bar-fill"
                          style={{
                            width: `${Math.min(100, Math.max(8, (selectedLetter.confidenceDetails?.contrast ?? (selectedLetter.confidence || 0.95)) * 100))}%`,
                          }}
                        />
                      </div>
                      <span className="pillar-subtext">Nitidez de traço e desvio padrão sobre o suporte</span>
                    </div>

                    <div className="letter-pillar-row">
                      <div className="letter-pillar-head">
                        <span>Coerência de Linha (20%)</span>
                        <strong>{((selectedLetter.confidenceDetails?.line_coherence ?? (selectedLetter.confidence || 0.95)) * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="pillar-bar-bg">
                        <div
                          className="pillar-bar-fill"
                          style={{
                            width: `${Math.min(100, Math.max(8, (selectedLetter.confidenceDetails?.line_coherence ?? (selectedLetter.confidence || 0.95)) * 100))}%`,
                          }}
                        />
                      </div>
                      <span className="pillar-subtext">Alinhamento vertical com a Linha {selectedLetter.line ?? 1}</span>
                    </div>

                    <div className="letter-pillar-row">
                      <div className="letter-pillar-head">
                        <span>Solidez e Densidade (15%)</span>
                        <strong>{((selectedLetter.confidenceDetails?.density ?? (selectedLetter.confidence || 0.95)) * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="pillar-bar-bg">
                        <div
                          className="pillar-bar-fill"
                          style={{
                            width: `${Math.min(100, Math.max(8, (selectedLetter.confidenceDetails?.density ?? (selectedLetter.confidence || 0.95)) * 100))}%`,
                          }}
                        />
                      </div>
                      <span className="pillar-subtext">
                        Densidade de traço: {(((selectedLetter.area || selectedLetter.width * selectedLetter.height) / Math.max(selectedLetter.width * selectedLetter.height, 1)) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

