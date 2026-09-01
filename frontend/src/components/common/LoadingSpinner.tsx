import React from 'react';
import './common.css';

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>Processando imagem...</p>
    </div>
  );
};