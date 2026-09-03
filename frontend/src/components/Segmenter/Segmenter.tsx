// frontend/src/components/Segmenter/Segmenter.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  ScanSearch,
  Sun,
  Moon,
  GitCompare,
  RotateCw,
  Search,
  X,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Layers,
  FileText,
  Percent,
  SlidersHorizontal,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { useSegmenter } from '../../hooks/useSegmenter';
import { useImageUpload } from '../../hooks/useImageUpload';
import { ImageUploader } from '../ImageUploader';
import { LetterGrid } from '../LetterGrid';
import { ControlPanel } from '../ControlPanel';
import { PipelineViewer } from '../PipelineViewer';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { ProcessingOptions, ComparisonResult, HistoryEntry, SegmentResult } from '../../types';
import { compareImages, getProcessingHistory, searchProcessingHistory, getHistoryItem, saveProcessingResult } from '../../services/api';
import './Segmenter.css';

export const Segmenter: React.FC = () => {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [showMobileControls, setShowMobileControls] = useState(false);
  const sourceUpload = useImageUpload();
  const comparisonUpload = useImageUpload();
  const { loading, error: segmentError, result, segment, reset } = useSegmenter();
  const [compareResult, setCompareResult] = useState<ComparisonResult | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedHistoryResult, setSelectedHistoryResult] = useState<SegmentResult | null>(null);
  const displayedResult = selectedHistoryResult ?? result;

  const [options, setOptions] = useState<ProcessingOptions>({
    sensitivity: 0.44,
    padding: 4,
    minLetterSize: 5,
    maxLetterSize: 200,
    removeNoise: true,
    thresholdMode: 'auto',
    maxImageSize: 1800,
    mode: 'enhanced',
    splitGroupedLetters: true,
    filterNonLetters: true,
  });

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await getProcessingHistory();
      setHistory(data);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const runHistorySearch = useCallback(async (query: string) => {
    setHistoryLoading(true);
    try {
      const data = await searchProcessingHistory(query);
      setHistory(data);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    const query = searchQuery.trim();

    if (!query) {
      void loadHistory();
      return;
    }

    const debounce = setTimeout(() => {
      void runHistorySearch(query);
    }, 350);

    return () => clearTimeout(debounce);
  }, [searchQuery, loadHistory, runHistorySearch]);

  const handleHistoryRefresh = () => {
    const query = searchQuery.trim();
    if (query) {
      void runHistorySearch(query);
    } else {
      void loadHistory();
    }
  };

  const handleClearSearch = () => setSearchQuery('');

  const highlightMatch = (text: string, query: string): React.ReactNode => {
    const term = query.trim();
    if (!term) return text;

    const index = text.toLowerCase().indexOf(term.toLowerCase());
    if (index === -1) return text;

    return (
      <>
        {text.slice(0, index)}
        <mark className="history-highlight">{text.slice(index, index + term.length)}</mark>
        {text.slice(index + term.length)}
      </>
    );
  };

  const handleOptionsChange = (newOptions: Partial<ProcessingOptions>) => {
    setOptions(prev => ({ ...prev, ...newOptions }));
  };

  const handleSegment = async () => {
    if (!sourceUpload.image) return;
    const nextResult = await segment(sourceUpload.image, options, sourceUpload.file?.name);
    if (nextResult) {
      handleHistoryRefresh();
    }
  };

  const handleCompare = async () => {
    if (!sourceUpload.image || !comparisonUpload.image) return;

    setCompareLoading(true);
    try {
      const data = await compareImages(sourceUpload.image, comparisonUpload.image, options);
      setCompareResult(data);
    } finally {
      setCompareLoading(false);
    }
  };

  const handleReset = () => {
    reset();
    sourceUpload.resetImage();
    comparisonUpload.resetImage();
    setCompareResult(null);
    setSelectedHistoryResult(null);
  };

  const handleSaveHistory = async () => {
    if (!displayedResult) return;

    setSaveLoading(true);
    setSaveError(null);
    try {
      const payload = {
        imageData: displayedResult.debugImage ?? sourceUpload.image ?? '',
        sourceName: sourceUpload.file?.name ?? 'imagem-processada.png',
        transcript: displayedResult.transcript ?? '',
        letters: displayedResult.letters ?? [],
        metadata: displayedResult.meta ?? {},
      };

      await saveProcessingResult(payload);
      handleHistoryRefresh();
    } catch (err: any) {
      const backendMessage = err?.response?.data?.error;
      setSaveError(
        backendMessage ||
          'Não foi possível salvar no histórico. Verifique a conexão com o backend/MongoDB.'
      );
    } finally {
      setSaveLoading(false);
    }
  };

  const handleHistorySelect = async (itemId: string) => {
    try {
      const item = await getHistoryItem(itemId);
      if (!item) return;

      const nextResult: SegmentResult = {
        letters: (item.letters ?? []).map((letter, index) => ({
          ...letter,
          id: typeof letter.id === 'number' ? letter.id : index + 1,
        })),
        debugImage: item.imageData ?? '',
        transcript: item.transcript ?? item.metadata?.transcript ?? '',
        meta: {
          width: 0,
          height: 0,
          totalLetters: item.metadata?.totalLetters ?? (item.letters?.length ?? 0),
          processingTime: item.metadata?.processingTime ?? 0,
          confidenceScore: item.metadata?.confidenceScore ?? 0,
          transcript: item.metadata?.transcript ?? item.transcript ?? '',
        },
        confidence: item.metadata?.confidenceScore ?? 0,
      };

      setSelectedHistoryResult(nextResult);
      setCompareResult(null);
    } catch {
      setSelectedHistoryResult(null);
    }
  };

  const handleDownloadAll = async () => {
    if (!result?.letters?.length) return;

    const JSZip = (await import('jszip')).default;
    const zip = new JSZip();

    const orderedLetters = [...result.letters];
    const transcript = result.transcript || orderedLetters
      .map((letter, index) => `${letter.id ?? index + 1}`)
      .join(' ');

    zip.file('transcricao.txt', `${transcript}\n`);

    orderedLetters.forEach((letter, index) => {
      if (!letter.image) return;

      const match = letter.image.match(/^data:image\/([a-zA-Z0-9.+-]+);base64,(.*)$/);
      if (!match) return;

      const extension = match[1] === 'jpeg' ? 'jpg' : match[1] || 'png';
      zip.file(`letras/letra_${String(letter.id ?? index + 1).padStart(3, '0')}.${extension}`, match[2], {
        base64: true,
      });
    });

    const blob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'letras-segmentadas.zip';
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const error = sourceUpload.error || comparisonUpload.error || segmentError;

  return (
    <div className="segmenter-container">
      {/* Top Header Bar */}
      <header className="segmenter-header">
        <div className="segmenter-header-row">
          <div className="brand-identity">
            <div className="brand-logo-box">
              <ScanSearch size={22} className="brand-logo-icon" />
            </div>
            <div>
              <div className="brand-title-wrap">
                <h1>Pattern Checker</h1>
                <span className="brand-badge">CV Studio v2.0</span>
              </div>
              <p>Segmentação morfológica, visão computacional e análise de similaridade textual</p>
            </div>
          </div>

          <div className="header-actions">
            <div className="backend-status-pill">
              <span className="status-live-dot" />
              <span>Sistema Pronto</span>
            </div>

            <button
              type="button"
              className="mobile-controls-toggle"
              onClick={() => setShowMobileControls(!showMobileControls)}
              aria-label="Abrir configurações de processamento"
            >
              <SlidersHorizontal size={16} />
              <span>Ajustes</span>
            </button>

            <button
              type="button"
              className="theme-toggle"
              onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
              aria-label="Alternar tema claro/escuro"
              title={`Mudar para modo ${theme === 'dark' ? 'claro' : 'escuro'}`}
            >
              {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
              <span className="theme-label">{theme === 'dark' ? 'Escuro' : 'Claro'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="segmenter-content">
        {/* Sidebar Controls Panel */}
        <aside className={`controls-panel ${showMobileControls ? 'mobile-open' : ''}`}>
          <ControlPanel
            options={options}
            onChange={handleOptionsChange}
            onSegment={handleSegment}
            onSave={handleSaveHistory}
            onReset={handleReset}
            loading={loading || compareLoading}
            saveLoading={saveLoading}
            hasImage={!!sourceUpload.image}
            hasResult={!!displayedResult?.letters?.length}
          />
        </aside>

        {/* Primary Content Area */}
        <main className="main-content">
          {/* Upload Cards Grid */}
          <div className="compare-grid">
            <div className="upload-card">
              <div className="upload-card-header">
                <div className="card-header-label">
                  <span className={`status-dot ${sourceUpload.image ? 'active' : ''}`} />
                  <span>Imagem de Origem (Amostra)</span>
                </div>
                {sourceUpload.image && (
                  <span className="card-badge-ready">Carregada</span>
                )}
              </div>
              <ImageUploader
                onImageUpload={sourceUpload.uploadImage}
                image={sourceUpload.image}
                debugImage={result?.debugImage}
                debugCount={result?.letters.length ?? 0}
                onReset={sourceUpload.resetImage}
                fileName={sourceUpload.file?.name}
              />
            </div>

            <div className="upload-card">
              <div className="upload-card-header">
                <div className="card-header-label">
                  <span className={`status-dot ${comparisonUpload.image ? 'active' : ''}`} />
                  <span>Imagem de Comparação (Opcional)</span>
                </div>
                {comparisonUpload.image && (
                  <span className="card-badge-ready">Carregada</span>
                )}
              </div>
              <ImageUploader
                onImageUpload={comparisonUpload.uploadImage}
                image={comparisonUpload.image}
                onReset={comparisonUpload.resetImage}
                fileName={comparisonUpload.file?.name}
              />
            </div>
          </div>

          {/* Compare Action Bar */}
          <div className="compare-actions">
            <button
              className="btn btn-compare"
              onClick={handleCompare}
              disabled={loading || compareLoading || !sourceUpload.image || !comparisonUpload.image}
            >
              <GitCompare size={17} />
              <span>{compareLoading ? 'Comparando Similaridade...' : 'Comparar Conteúdo das Imagens'}</span>
            </button>
          </div>

          {/* Loading Indicator */}
          {loading && (
            <LoadingSpinner
              label="Executando Visão Computacional..."
              subtext="Filtro bilateral, binarização Otsu, Canny e extração de contornos em andamento"
            />
          )}
          {compareLoading && (
            <LoadingSpinner
              label="Calculando Similaridade Textual..."
              subtext="Segmentando ambas as imagens e calculando matriz de correspondência"
            />
          )}

          {/* Error Message */}
          {error && <ErrorMessage message={error} />}

          {/* Comparison Result Banner */}
          {compareResult && (
            <div className={`comparison-panel ${compareResult.status}`}>
              <div className="comparison-header">
                <div className="comparison-title-wrap">
                  <span className="comparison-eyebrow">Diagnóstico de Correspondência</span>
                  <div className="comparison-status-badge">
                    {compareResult.status === 'plagio_detectado' ? (
                      <>
                        <AlertTriangle size={20} className="status-badge-icon danger" />
                        <h3>Plágio Detectado</h3>
                      </>
                    ) : compareResult.status === 'imagem_aceita' ? (
                      <>
                        <CheckCircle2 size={20} className="status-badge-icon success" />
                        <h3>Imagem Aceita (Original)</h3>
                      </>
                    ) : (
                      <>
                        <AlertCircle size={20} className="status-badge-icon warning" />
                        <h3>Semelhança Parcial</h3>
                      </>
                    )}
                  </div>
                </div>

                <div className="comparison-score-box">
                  <span className="score-label">Índice de Semelhança</span>
                  <strong className="score-value">
                    {((compareResult.similarity ?? 0) * 100).toFixed(1)}%
                  </strong>
                </div>
              </div>

              {/* Score Progress Bar */}
              <div className="comparison-progress-track">
                <div
                  className="comparison-progress-fill"
                  style={{ width: `${Math.min(100, Math.max(0, (compareResult.similarity ?? 0) * 100))}%` }}
                />
              </div>

              <p className="comparison-verdict">{compareResult.verdict}</p>

              <div className="comparison-metrics">
                <div className="metric-card">
                  <div className="metric-icon-wrap">
                    <Percent size={16} />
                  </div>
                  <div className="metric-data">
                    <span>Semelhança Calculada</span>
                    <strong>{((compareResult.similarity ?? 0) * 100).toFixed(1)}%</strong>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon-wrap">
                    <FileText size={16} />
                  </div>
                  <div className="metric-data">
                    <span>Caracteres (Amostra 1)</span>
                    <strong>{compareResult.sourceLetters ?? 0} letras</strong>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon-wrap">
                    <Layers size={16} />
                  </div>
                  <div className="metric-data">
                    <span>Caracteres (Amostra 2)</span>
                    <strong>{compareResult.targetLetters ?? 0} letras</strong>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Quality Notice / Warnings */}
          {displayedResult && displayedResult.meta.warnings && displayedResult.meta.warnings.length > 0 && (
            <section className="quality-notice" aria-label="Limitações da análise">
              <div className="quality-notice-header">
                <ShieldAlert size={20} className="quality-notice-icon" />
                <div>
                  <span className="quality-notice-label">Diagnóstico de Qualidade & Limitações</span>
                  <h3>Observações sobre a Qualidade da Imagem</h3>
                </div>
              </div>
              <ul className="quality-notice-list">
                {displayedResult.meta.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Letter Grid Results */}
          {displayedResult && (
            <LetterGrid
              letters={displayedResult.letters}
              onDownload={handleDownloadAll}
              metadata={displayedResult.meta}
            />
          )}

          {/* Pipeline Step Viewer */}
          <PipelineViewer
            steps={displayedResult?.steps ?? []}
            warnings={displayedResult?.meta?.warnings ?? []}
            splitsCount={displayedResult?.meta?.splits_count ?? 0}
            filteredCount={displayedResult?.meta?.filtered_count ?? 0}
            mode={options.mode}
          />

          {/* History Panel */}
          <div className="history-panel">
            <div className="history-header">
              <div className="history-title-wrap">
                <Clock size={17} className="history-title-icon" />
                <h3>Histórico de Processamentos</h3>
              </div>
              <button
                type="button"
                className={`history-refresh ${historyLoading ? 'loading' : ''}`}
                onClick={handleHistoryRefresh}
                title="Recarregar histórico"
              >
                <RotateCw size={13} className={historyLoading ? 'spin-icon' : ''} />
                <span>{historyLoading ? 'Atualizando...' : 'Atualizar'}</span>
              </button>
            </div>

            <div className={`history-search ${searchQuery ? 'has-value' : ''}`}>
              <Search size={15} className="history-search-icon" />
              <input
                type="text"
                className="history-search-input"
                placeholder="Buscar por nome do arquivo salvo..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Buscar imagens salvas no histórico"
              />
              {historyLoading && searchQuery && (
                <span className="history-search-spinner" aria-hidden="true" />
              )}
              {searchQuery && !historyLoading && (
                <button
                  type="button"
                  className="history-search-clear"
                  onClick={handleClearSearch}
                  aria-label="Limpar busca"
                >
                  <X size={12} />
                </button>
              )}
            </div>

            {searchQuery.trim() && !historyLoading && (
              <p className="history-search-status">
                {history.length > 0
                  ? `${history.length} ${history.length === 1 ? 'resultado encontrado' : 'resultados encontrados'} para "${searchQuery.trim()}"`
                  : `Nenhuma imagem encontrada para "${searchQuery.trim()}".`}
              </p>
            )}

            {saveError && <p className="history-error">{saveError}</p>}

            <div className="history-list">
              {history.length === 0 && !searchQuery.trim() ? (
                <div className="history-empty">
                  <p>Nenhuma imagem salva no histórico até o momento.</p>
                  <small>Clique em "Salvar" no painel de configurações para arquivar resultados.</small>
                </div>
              ) : (
                history.map((entry, index) => (
                  <button
                    key={entry._id ?? entry.sourceName}
                    type="button"
                    className="history-item"
                    style={{ animationDelay: `${index * 35}ms` }}
                    onClick={() => void handleHistorySelect(entry._id ?? '')}
                  >
                    <div className="history-item-top">
                      {entry.imageData && (
                        <img
                          src={entry.imageData}
                          alt={entry.sourceName ?? 'Imagem processada'}
                          className="history-thumb"
                        />
                      )}
                      <div className="history-item-info">
                        <span className="history-name">
                          {highlightMatch(entry.sourceName ?? 'Imagem processada', searchQuery)}
                        </span>
                        <span className="history-meta">
                          {entry.createdAt ? new Date(entry.createdAt).toLocaleString('pt-BR') : 'Hoje'}
                        </span>
                        {entry.letters && entry.letters.length > 0 && (
                          <span className="history-letters-count">
                            {entry.letters.length} caracteres extraídos
                          </span>
                        )}
                      </div>
                    </div>

                    {entry.letters && entry.letters.length > 0 ? (
                      <div className="history-letters-strip">
                        {entry.letters.slice(0, 14).map((letter, letterIdx) =>
                          letter.image ? (
                            <img
                              key={letter.id ?? letterIdx}
                              src={letter.image}
                              alt={`Caractere ${letter.id ?? letterIdx + 1}`}
                              className="history-letter-thumb"
                            />
                          ) : (
                            <span key={letter.id ?? letterIdx} className="history-letter-thumb-placeholder">
                              {letter.id ?? letterIdx + 1}
                            </span>
                          )
                        )}
                        {entry.letters.length > 14 && (
                          <span className="history-more-pill">+{entry.letters.length - 14}</span>
                        )}
                      </div>
                    ) : (
                      <span className="history-transcript">Sem recortes salvos</span>
                    )}

                    <div className="history-item-footer">
                      <span className="history-view-hint">
                        Carregar no Editor
                        <ArrowRight size={13} />
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

