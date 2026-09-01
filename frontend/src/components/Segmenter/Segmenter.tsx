// frontend/src/components/Segmenter/Segmenter.tsx
import React from 'react';
import { useSegmenter } from '../../hooks/useSegmenter';
import { useImageUpload } from '../../hooks/useImageUpload';
import { ImageUploader } from '../ImageUploader';
import { LetterGrid } from '../LetterGrid';
import { ControlPanel } from '../ControlPanel';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { ProcessingOptions, ComparisonResult } from '../../types';
import { compareImages } from '../../services/api';
import './Segmenter.css';

export const Segmenter: React.FC = () => {
  const sourceUpload = useImageUpload();
  const comparisonUpload = useImageUpload();
  const { loading, error: segmentError, result, segment, reset } = useSegmenter();
  const [compareResult, setCompareResult] = React.useState<ComparisonResult | null>(null);
  const [compareLoading, setCompareLoading] = React.useState(false);

  const [options, setOptions] = React.useState<ProcessingOptions>({
    sensitivity: 0.44,
    padding: 4,
    minLetterSize: 5,
    maxLetterSize: 200,
    removeNoise: true,
    thresholdMode: 'auto',
    maxImageSize: 1800,
  });

  const handleOptionsChange = (newOptions: Partial<ProcessingOptions>) => {
    setOptions(prev => ({ ...prev, ...newOptions }));
  };

  const handleSegment = async () => {
    if (!sourceUpload.image) return;
    await segment(sourceUpload.image, options);
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
        <h1>Pattern Checker</h1>
        <p>Segmentação, comparação e validação de semelhança entre imagens de texto</p>
      </header>

      <div className="segmenter-content">
        <aside className="controls-panel">
          <ControlPanel
            options={options}
            onChange={handleOptionsChange}
            onSegment={handleSegment}
            onReset={handleReset}
            loading={loading || compareLoading}
            hasImage={!!sourceUpload.image}
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

          {result && (
            <LetterGrid
              letters={result.letters}
              onDownload={handleDownloadAll}
              metadata={result.meta}
            />
          )}
        </main>
      </div>
    </div>
  );
};
