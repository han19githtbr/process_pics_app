import React from 'react';
import { Letter } from '../../types';
import './LetterGrid.css';

interface LetterGridProps {
  letters: Letter[];
  onDownload: () => void;
  metadata?: {
    totalLetters: number;
    processingTime: number;
    confidenceScore: number;
  };
}

export const LetterGrid: React.FC<LetterGridProps> = ({
  letters,
  onDownload,
  metadata,
}) => {
  const orderedLetters = [...letters];

  if (orderedLetters.length === 0) {
    return (
      <div className="letter-grid-empty">
        <p>Nenhuma letra encontrada.</p>
        <p>Tente ajustar os parâmetros ou verificar a imagem.</p>
      </div>
    );
  }

  return (
    <div className="letter-grid-container">
      <div className="letter-grid-header">
        <div className="header-left">
          <h2>Letras Encontradas</h2>
          <span className="letter-count">{orderedLetters.length} letras</span>
        </div>
        <div className="header-right">
          {metadata && (
            <span className="metadata">
              Confiança: {(metadata.confidenceScore * 100).toFixed(1)}%
            </span>
          )}
          <button onClick={onDownload} className="btn-download">
            📥 Baixar Todas
          </button>
        </div>
      </div>

      <div className="letter-transcript">
        <span className="transcript-label">Texto reconstruído em ordem de leitura:</span>
        <div className="transcript-strip">
          {orderedLetters.map((letter, index) => (
            <div key={letter.id ?? `${letter.x}-${letter.y}-${index}`} className="transcript-card">
              {letter.image ? (
                <img src={letter.image} alt={`Letra recortada ${letter.id ?? index + 1}`} className="transcript-image" />
              ) : (
                <div className="transcript-placeholder">{index + 1}</div>
              )}
              <span className="transcript-number">#{letter.id ?? index + 1}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="letter-grid">
        {orderedLetters.map((letter, index) => (
          <div key={letter.id ?? `${letter.x}-${letter.y}-${index}`} className="letter-item">
            {letter.image ? (
              <img
                src={letter.image}
                alt={`Letra ${letter.id ?? index + 1}`}
                className="letter-image"
              />
            ) : (
              <div className="letter-placeholder">
                <span>{index + 1}</span>
              </div>
            )}
            <div className="letter-info">
              <span className="letter-id">#{letter.id ?? index + 1}</span>
              {letter.line && (
                <span className="letter-line">Linha {letter.line}</span>
              )}
              <span className="letter-confidence">
                {((letter.confidence || 0) * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
