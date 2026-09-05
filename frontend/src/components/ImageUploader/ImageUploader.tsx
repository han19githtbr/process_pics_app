import React, { useRef, useState, useId, useEffect } from 'react';
import {
  UploadCloud,
  Image as ImageIcon,
  Trash2,
  RotateCw,
  FolderOpen,
  Layers,
  ZoomIn,
  X,
  Sparkles,
} from 'lucide-react';
import './ImageUploader.css';

interface ImageUploaderProps {
  onImageUpload: (file: File) => void;
  image: string | null;
  debugImage?: string;
  debugCount?: number;
  onReset?: () => void;
  fileName?: string;
  /**
   * Incremente este número (ex.: a cada mudança de parâmetro) para forçar
   * a exibição automática da aba "Debug" — usado para mostrar o efeito
   * ao vivo dos ajustes de Sensibilidade, Margem do recorte, etc. sem que
   * o usuário precise clicar manualmente na aba.
   */
  focusDebugSignal?: number;
  /**
   * true enquanto o preview ao vivo está sendo recalculado no backend após
   * um ajuste de parâmetro. Exibe um indicador "Atualizando…" sobre a
   * imagem de debug, para deixar claro que o efeito já está a caminho (e
   * não que nada está acontecendo até clicar em "Segmentar Imagem").
   */
  previewLoading?: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onImageUpload,
  image,
  debugImage,
  debugCount = 0,
  onReset,
  fileName,
  focusDebugSignal,
  previewLoading,
}) => {
  const inputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [activeView, setActiveView] = useState<'original' | 'debug'>('original');
  const [showModal, setShowModal] = useState(false);

  // Sempre que o pai sinaliza que um parâmetro de processamento mudou
  // (e há uma imagem carregada), muda automaticamente para a aba "Debug"
  // para que o efeito do ajuste apareça imediatamente, ao vivo.
  useEffect(() => {
    if (focusDebugSignal) {
      setActiveView('debug');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusDebugSignal]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onImageUpload(file);
      setActiveView('original');
    }
    // Permite selecionar o mesmo arquivo novamente caso o usuário queira recarregar
    event.target.value = '';
  };

  const handleDrop = (event: React.DragEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      onImageUpload(file);
      setActiveView('original');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const handleRotate = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!image) return;

    try {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      await new Promise<void>((resolve, reject) => {
        img.onload = () => resolve();
        img.onerror = () => reject(new Error('Falha ao carregar imagem para rotação'));
        img.src = image;
      });

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = img.naturalHeight || img.height;
      canvas.height = img.naturalWidth || img.width;

      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((90 * Math.PI) / 180);
      ctx.drawImage(img, -(img.naturalWidth || img.width) / 2, -(img.naturalHeight || img.height) / 2);

      canvas.toBlob((blob) => {
        if (!blob) return;
        const name = fileName ? fileName.replace(/\.[^.]+$/, '') + '.png' : 'imagem.png';
        const rotatedFile = new File([blob], name, { type: 'image/png' });
        onImageUpload(rotatedFile);
        setActiveView('original');
      }, 'image/png');
    } catch (err) {
      console.error('Erro ao girar imagem:', err);
    }
  };

  const displayedImage = (activeView === 'debug' && debugImage) ? debugImage : image;

  return (
    <div className="image-uploader">
      <input
        ref={fileInputRef}
        id={inputId}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        onChange={handleFileChange}
        style={{ display: 'none' }}
        aria-hidden="true"
      />

      {!image ? (
        <label
          htmlFor={inputId}
          className={`upload-area ${isDragging ? 'dragging' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          aria-label="Área de upload de imagem. Clique ou arraste um arquivo."
        >
          <div className="upload-content">
            <div className="upload-icon-box">
              <UploadCloud className="upload-icon" size={28} />
            </div>
            <h3>Carregue uma imagem</h3>
            <p>Arraste e solte ou clique para navegar</p>
            <div className="upload-format-badges">
              <span className="badge-pill">PNG</span>
              <span className="badge-pill">JPG</span>
              <span className="badge-pill">JPEG</span>
              <span className="badge-pill size-limit">Máx 10 MB</span>
            </div>
          </div>
        </label>
      ) : (
        <div
          className={`image-preview-card ${isDragging ? 'dragging' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className="preview-toolbar">
            <div className="preview-meta">
              <ImageIcon size={16} className="preview-icon" />
              <span className="preview-filename" title={fileName || 'Imagem carregada'}>
                {fileName || 'Imagem carregada'}
              </span>
            </div>

            <div className="preview-actions">
              {debugImage && (
                <div className="preview-view-toggle">
                  <button
                    type="button"
                    className={`toggle-tab-btn ${activeView === 'original' ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveView('original');
                    }}
                    title="Exibir imagem original"
                  >
                    Original
                  </button>
                  <button
                    type="button"
                    className={`toggle-tab-btn ${activeView === 'debug' ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveView('debug');
                    }}
                    title="Exibir segmentação com contornos e bounding boxes"
                  >
                    <Sparkles size={12} />
                    Debug ({debugCount})
                  </button>
                </div>
              )}

              <button
                type="button"
                className="btn-icon-action"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowModal(true);
                }}
                title="Ampliar visualização (Zoom)"
                aria-label="Ampliar visualização"
              >
                <ZoomIn size={15} />
              </button>

              <button
                type="button"
                className="btn-icon-action"
                onClick={handleRotate}
                title="Girar imagem 90° no sentido horário"
                aria-label="Girar imagem 90°"
              >
                <RotateCw size={14} />
              </button>

              <button
                type="button"
                className="btn-icon-action"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                title="Substituir imagem por outra"
                aria-label="Substituir imagem"
              >
                <FolderOpen size={14} />
              </button>

              {onReset && (
                <button
                  type="button"
                  className="btn-icon-action danger"
                  onClick={(e) => {
                    e.stopPropagation();
                    onReset();
                  }}
                  title="Remover imagem"
                  aria-label="Remover imagem"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          </div>

          <div className="image-viewport">
            {displayedImage && (
              <img
                src={displayedImage}
                alt={activeView === 'debug' ? 'Debug de segmentação' : 'Preview da imagem'}
                className="preview-image"
              />
            )}

            {/* Indicador ao vivo: aparece assim que um parâmetro muda, para deixar
                claro que o efeito já está sendo recalculado (evita a impressão de
                que "nada muda" enquanto se aguarda o resultado chegar do backend). */}
            {activeView === 'debug' && previewLoading && (
              <div className="live-preview-updating-badge" role="status" aria-live="polite">
                <span className="live-preview-spinner" aria-hidden="true" />
                <span>Atualizando pré-visualização…</span>
              </div>
            )}

            {debugImage && (
              <button
                type="button"
                className={`floating-debug-badge ${activeView === 'debug' ? 'active' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveView(activeView === 'debug' ? 'original' : 'debug');
                }}
                title={activeView === 'debug' ? 'Voltar para a imagem original' : 'Visualizar bounding boxes e contornos'}
              >
                <Layers size={13} />
                <span>
                  {activeView === 'debug'
                    ? `${debugCount} letras — Ver Imagem Original`
                    : `${debugCount} letras detectadas — Ver Bounding Boxes`}
                </span>
              </button>
            )}
          </div>
        </div>
      )}

      {showModal && displayedImage && (
        <div className="image-lightbox-backdrop" onClick={() => setShowModal(false)}>
          <div className="image-lightbox-content" onClick={(e) => e.stopPropagation()}>
            <div className="lightbox-header">
              <h4>{activeView === 'debug' ? 'Visão de Segmentação (Debug)' : (fileName || 'Imagem Original')}</h4>
              <button
                type="button"
                className="lightbox-close-btn"
                onClick={() => setShowModal(false)}
                aria-label="Fechar ampliação"
              >
                <X size={18} />
              </button>
            </div>
            <div className="lightbox-img-wrapper">
              <img src={displayedImage} alt="Visualização em alta resolução" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
