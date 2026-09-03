import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  Image as ImageIcon,
  Trash2,
  RefreshCw,
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
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onImageUpload,
  image,
  debugImage,
  debugCount = 0,
  onReset,
  fileName,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [activeView, setActiveView] = useState<'original' | 'debug'>('original');
  const [showModal, setShowModal] = useState(false);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onImageUpload(file);
      setActiveView('original');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      onImageUpload(file);
      setActiveView('original');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const displayedImage = (activeView === 'debug' && debugImage) ? debugImage : image;

  return (
    <div className="image-uploader">
      {!image ? (
        <div
          className={`upload-area ${isDragging ? 'dragging' : ''}`}
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') handleClick();
          }}
          aria-label="Área de upload de imagem"
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
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleFileChange}
            className="file-input"
          />
        </div>
      ) : (
        <div className="image-preview-card">
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
                    onClick={() => setActiveView('original')}
                    title="Exibir imagem original"
                  >
                    Original
                  </button>
                  <button
                    type="button"
                    className={`toggle-tab-btn ${activeView === 'debug' ? 'active' : ''}`}
                    onClick={() => setActiveView('debug')}
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
                onClick={() => setShowModal(true)}
                title="Ampliar visualização"
                aria-label="Ampliar visualização"
              >
                <ZoomIn size={15} />
              </button>

              <button
                type="button"
                className="btn-icon-action"
                onClick={handleClick}
                title="Substituir imagem"
                aria-label="Substituir imagem"
              >
                <RefreshCw size={14} />
              </button>

              {onReset && (
                <button
                  type="button"
                  className="btn-icon-action danger"
                  onClick={onReset}
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

            {debugImage && activeView === 'original' && (
              <button
                type="button"
                className="floating-debug-badge"
                onClick={() => setActiveView('debug')}
              >
                <Layers size={13} />
                <span>{debugCount} letras detectadas — Ver Bounding Boxes</span>
              </button>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleFileChange}
            className="file-input"
          />
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

