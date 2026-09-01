import React from 'react';
import './common.css';

interface ErrorMessageProps {
  message: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  return (
    <div className="error-container">
      <span className="error-icon">⚠️</span>
      <p className="error-message">{message}</p>
    </div>
  );
};