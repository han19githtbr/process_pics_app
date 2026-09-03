import React from 'react';
import './common.css';

interface LoadingSpinnerProps {
  label?: string;
  subtext?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Processando visão computacional...',
  subtext = 'Executando filtragem, binarização e detecção de contornos',
}) => {
  return (
    <div className="loading-container">
      <div className="spinner-wrapper">
        <div className="spinner-pulse" />
        <div className="spinner" />
      </div>
      <p className="loading-text">{label}</p>
      {subtext && <p className="loading-subtext">{subtext}</p>}
    </div>
  );
};