// frontend/src/components/Segmenter/Segmenter.tsx
import React from 'react';
import { useSegmenter } from '../../hooks/useSegmenter';
import { useImageUpload } from '../../hooks/useImageUpload';
import { ImageUploader } from '../ImageUploader';
import { LetterGrid } from '../LetterGrid';
import { ControlPanel } from '../ControlPanel';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { ProcessingOptions, ComparisonResult, HistoryEntry, SegmentResult } from '../../types';
import { compareImages, getProcessingHistory, getHistoryItem, saveProcessingResult } from '../../services/api';
import './Segmenter.css';

export const Segmenter: React.FC = () => {
  const [theme, setTheme] = React.useState<'dark' | 'light'>('dark');
  const sourceUpload = useImageUpload();
  const comparisonUpload = useImageUpload();
  const { loading, error: segmentError, result, segment, reset } = useSegmenter();
  const [compareResult, setCompareResult] = React.useState<ComparisonResult | null>(null);
  const [compareLoading, setCompareLoading] = React.useState(false);
  const [saveLoading, setSaveLoading] = React.useState(false);
  const [saveError, setSaveError] = React.useState<string | null>(null);
  const [history, setHistory] = React.useState<HistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = React.useState(false);
  const [selectedHistoryResult, setSelectedHistoryResult] = React.useState<SegmentResult | null>(null);
  const displayedResult = selectedHistoryResult ?? result;

  const [options, setOptions] = React.useState<ProcessingOptions>({
    sensitivity: 0.44,
    padding: 4,
    minLetterSize: 5,
    maxLetterSize: 200,
    removeNoise: true,
    thresholdMode: 'auto',
    maxImageSize: 1800,
  });

  const loadHistory = React.useCallback(async () => {
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

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  React.useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const handleOptionsChange = (newOptions: Partial<ProcessingOptions>) => {
    setOptions(prev => ({ ...prev, ...newOptions }));
  };

  const handleSegment = async () => {
    if (!sourceUpload.image) return;
    const nextResult = await segment(sourceUpload.image, options, sourceUpload.file?.name);
    if (nextResult) {
      await loadHistory();
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
      await loadHistory();
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
      <header className="segmenter-header">
        <div className="segmenter-header-row">
          <h1>Pattern Checker</h1>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
            aria-label="Alternar entre modo claro e escuro"
          >
            <span>{theme === 'dark' ? '🌙' : '☀️'}</span>
            <span className="theme-toggle-track" aria-hidden="true">
              <span className="theme-toggle-thumb" />
            </span>
          </button>
        </div>
        <p>Segmentação, comparação e validação de semelhança entre imagens de texto</p>
      </header>

      <div className="segmenter-content">
        <aside className="controls-panel">
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

        <main className="main-content">
          <div className="compare-grid">
            <div className="upload-card">
              <div className="upload-card-header">
                <span>Imagem original</span>
                <span className="status-dot active" />
              </div>
              <ImageUploader
                onImageUpload={sourceUpload.uploadImage}
                image={sourceUpload.image}
                debugImage={result?.debugImage}
                debugCount={result?.letters.length ?? 0}
              />
            </div>

            <div className="upload-card">
              <div className="upload-card-header">
                <span>Imagem de comparação</span>
                <span className="status-dot" />
              </div>
              <ImageUploader
                onImageUpload={comparisonUpload.uploadImage}
                image={comparisonUpload.image}
              />
            </div>
          </div>

          <div className="compare-actions">
            <button
              className="btn btn-compare"
              onClick={handleCompare}
              disabled={loading || compareLoading || !sourceUpload.image || !comparisonUpload.image}
            >
              {compareLoading ? '⏳ Comparando...' : 'Comparar conteúdo'}
            </button>
          </div>

          <div className="history-panel">
            <div className="history-header">
              <h3>Histórico</h3>
              <button type="button" className="history-refresh" onClick={() => void loadHistory()}>
                {historyLoading ? 'Atualizando...' : 'Atualizar'}
              </button>
            </div>
            {saveError && <p className="history-error">{saveError}</p>}
            <div className="history-list">
              {history.length === 0 ? (
                <p className="history-empty">Ainda não há imagens salvas no histórico.</p>
              ) : (
                history.map((entry) => (
                  <button
                    key={entry._id ?? entry.sourceName}
                    type="button"
                    className="history-item"
                    onClick={() => void handleHistorySelect(entry._id ?? '')}
                  >
                    {entry.imageData && (
                      <img src={entry.imageData} alt={entry.sourceName ?? 'Imagem processada'} className="history-thumb" />
                    )}
                    <span className="history-name">{entry.sourceName ?? 'Imagem processada'}</span>
                    <span className="history-meta">
                      {entry.createdAt ? new Date(entry.createdAt).toLocaleString('pt-BR') : 'Agora'}
                    </span>
                    <span className="history-transcript">{entry.transcript ?? 'Sem transcrição'}</span>
                  </button>
                ))
              )}
            </div>
          </div>

          {loading && <LoadingSpinner />}
          {compareLoading && <LoadingSpinner />}

          {error && <ErrorMessage message={error} />}

          {compareResult && (
            <div className="comparison-panel">
              <div className="comparison-header">
                <div>
                  <span className="comparison-eyebrow">Análise de similaridade</span>
                  <h3>{compareResult.status === 'plagio_detectado' ? 'Plágio detectado' : compareResult.status === 'imagem_aceita' ? 'Imagem aceita' : 'Semelhança parcial'}</h3>
                </div>
                <div className="comparison-score">
                  {(compareResult.similarity ?? 0) * 100}%
                </div>
              </div>

              <p className="comparison-verdict">{compareResult.verdict}</p>

              <div className="comparison-metrics">
                <div className="metric-card">
                  <span>Semelhança</span>
                  <strong>{((compareResult.similarity ?? 0) * 100).toFixed(1)}%</strong>
                </div>
                <div className="metric-card">
                  <span>Fonte 1</span>
                  <strong>{compareResult.sourceLetters ?? 0} letras</strong>
                </div>
                <div className="metric-card">
                  <span>Fonte 2</span>
                  <strong>{compareResult.targetLetters ?? 0} letras</strong>
                </div>
              </div>
            </div>
          )}

          {displayedResult && (
            <LetterGrid
              letters={displayedResult.letters}
              onDownload={handleDownloadAll}
              metadata={displayedResult.meta}
            />
          )}
        </main>
      </div>
    </div>
  );
};
