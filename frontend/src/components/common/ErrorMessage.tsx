import React from 'react';
import { AlertTriangle } from 'lucide-react';
import './common.css';

interface ErrorMessageProps {
  message: string;
  title?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  title = 'Falha no processamento',
}) => {
  return (
    <div className="error-container" role="alert">
      <AlertTriangle className="error-icon" size={20} />
      <div className="error-content">
        <h4 className="error-title">{title}</h4>
        <p className="error-message">{message}</p>
      </div>
    </div>
  );
};