import React, { useRef } from 'react';
import './ImageUploader.css';

interface ImageUploaderProps {
  onImageUpload: (file: File) => void;
  image: string | null;
  debugImage?: string;
  debugCount?: number;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onImageUpload,
  image,
  debugImage,
  debugCount = 0,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onImageUpload(file);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) {
      onImageUpload(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  return (
    <div className="image-uploader">
      {!image ? (
        <div
          className="upload-area"
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <div className="upload-content">
            <span className="upload-icon">📁</span>
            <h3>Selecione uma imagem</h3>
            <p>Clique ou arraste um arquivo</p>
            <p className="upload-hint">Suporta PNG, JPG ou JPEG</p>
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
        <div className="image-preview">
          <div className="image-container">
            <img src={image} alt="Preview" className="preview-image" />
            {debugImage && (
              <div className="debug-overlay" aria-label="Overlay de debug da segmentação">
                <div className="debug-header">
                  <span>Debug de segmentação</span>
                  <strong>{debugCount} letras em ordem de leitura</strong>
                </div>
                <img src={debugImage} alt="Debug da segmentação" className="debug-image" />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
