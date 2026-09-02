import React from 'react';
import { ProcessingOptions } from '../../types';
import './ControlPanel.css';

interface ControlPanelProps {
  options: ProcessingOptions;
  onChange: (options: Partial<ProcessingOptions>) => void;
  onSegment: () => void;
  onSave: () => void;
  onReset: () => void;
  loading: boolean;
  saveLoading: boolean;
  hasImage: boolean;
  hasResult: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  options,
  onChange,
  onSegment,
  onSave,
  onReset,
  loading,
  saveLoading,
  hasImage,
  hasResult,
}) => {
  const handleChange = <K extends keyof ProcessingOptions>(
    key: K,
    value: ProcessingOptions[K]
  ) => {
    onChange({ [key]: value });
  };

  const configCards = [
    {
      key: 'sensitivity',
      icon: '⚡',
      label: 'Sensibilidade',
      description: 'Define quão fácil o sistema reconhece marcas e letras.',
      hint: 'Mais alta = mais deteções, mais ruído.',
      value: `${options.sensitivity?.toFixed(2)}`,
      render: (
        <input
          type="range"
          min="0.1"
          max="0.8"
          step="0.01"
          value={options.sensitivity}
          onChange={(e) =>
            handleChange('sensitivity', parseFloat(e.target.value))
          }
        />
      ),
    },
    {
      key: 'padding',
      icon: '✂️',
      label: 'Margem do recorte',
      description: 'Adiciona espaço ao redor de cada letra para evitar cortes apertados.',
      hint: 'Útil para letras com bordas irregulares.',
      value: `${options.padding}px`,
      render: (
        <input
          type="range"
          min="0"
          max="10"
          step="1"
          value={options.padding}
          onChange={(e) =>
            handleChange('padding', parseInt(e.target.value))
          }
        />
      ),
    },
    {
      key: 'minLetterSize',
      icon: '🔎',
      label: 'Tamanho mínimo da letra',
      description: 'Ignora regiões muito pequenas que normalmente são ruído.',
      hint: 'Ajuda com elementos decorativos e marcas pequenas.',
      value: `${options.minLetterSize}px`,
      render: (
        <input
          type="range"
          min="2"
          max="20"
          step="1"
          value={options.minLetterSize}
          onChange={(e) =>
            handleChange('minLetterSize', parseInt(e.target.value))
          }
        />
      ),
    },
  ];

  return (
    <div className="control-panel">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Ajustes rápidos</span>
          <h3>Configurações</h3>
        </div>
        <span className="panel-badge">Live</span>
      </div>

      <div className="settings-stack">
        {configCards.map((setting) => (
          <div className="control-group" key={setting.key}>
            <div className="setting-topline">
              <div className="setting-title-wrap">
                <span className="setting-icon" aria-hidden="true">{setting.icon}</span>
                <div>
                  <label>{setting.label}</label>
                  <p>{setting.description}</p>
                </div>
              </div>
              <span className="value-pill">{setting.value}</span>
            </div>
            <div className="slider-wrap">{setting.render}</div>
            <small>{setting.hint}</small>
          </div>
        ))}

        <div className="mode-selector-group">
          <label className="mode-selector-label">Modo de Processamento:</label>
          <div className="mode-options-grid">
            <button
              type="button"
              className={`mode-btn ${options.mode !== 'academic' ? 'active' : ''}`}
              onClick={() => handleChange('mode', 'enhanced')}
            >
              <span className="mode-btn-title">✨ Aprimorado</span>
              <span className="mode-btn-desc">PDF + Separação de letras e filtro de ruído</span>
            </button>
            <button
              type="button"
              className={`mode-btn ${options.mode === 'academic' ? 'active' : ''}`}
              onClick={() => handleChange('mode', 'academic')}
            >
              <span className="mode-btn-title">🎓 Acadêmico Puro</span>
              <span className="mode-btn-desc">Exato do documento em PDF UFRRJ</span>
            </button>
          </div>
        </div>

        <div className="toggle-list">
          <label className="toggle-item">
            <input
              type="checkbox"
              checked={options.splitGroupedLetters !== false}
              onChange={(e) =>
                handleChange('splitGroupedLetters', e.target.checked)
              }
            />
            <span className="toggle-copy">
              <span className="toggle-headline">
                <span className="toggle-icon" aria-hidden="true">🔤</span>
                <strong>Separar letras coladas</strong>
              </span>
              <small>Desmembra grupos de caracteres via perfil de projeção vertical.</small>
            </span>
          </label>

          <label className="toggle-item">
            <input
              type="checkbox"
              checked={options.filterNonLetters !== false}
              onChange={(e) =>
                handleChange('filterNonLetters', e.target.checked)
              }
            />
            <span className="toggle-copy">
              <span className="toggle-headline">
                <span className="toggle-icon" aria-hidden="true">🎯</span>
                <strong>Filtrar elementos não-letras</strong>
              </span>
              <small>Rejeita linhas, molduras, sublinhados e ruídos que não são texto.</small>
            </span>
          </label>

          <label className="toggle-item">
            <input
              type="checkbox"
              checked={options.removeNoise}
              onChange={(e) =>
                handleChange('removeNoise', e.target.checked)
              }
            />
            <span className="toggle-copy">
              <span className="toggle-headline">
                <span className="toggle-icon" aria-hidden="true">🧹</span>
                <strong>Remover ruídos</strong>
              </span>
              <small>Elimina artefatos pequenos que não são letras.</small>
            </span>
          </label>

          <label className="toggle-item">
            <input
              type="checkbox"
              checked={options.enhanceContrast}
              onChange={(e) =>
                handleChange('enhanceContrast', e.target.checked)
              }
            />
            <span className="toggle-copy">
              <span className="toggle-headline">
                <span className="toggle-icon" aria-hidden="true">🌗</span>
                <strong>Melhorar contraste</strong>
              </span>
              <small>Aumenta a legibilidade do texto em imagens fracas.</small>
            </span>
          </label>
        </div>
      </div>

      <div className="button-group button-group-stack">
        <button
          onClick={onSegment}
          disabled={loading || !hasImage}
          className="btn btn-primary"
        >
          {loading ? '⏳ Processando...' : 'Segmentar'}
        </button>
        <button
          onClick={onReset}
          disabled={loading}
          className="btn btn-secondary"
        >
          Limpar
        </button>
        <button
          onClick={onSave}
          disabled={saveLoading || loading || !hasResult}
          className="btn btn-secondary"
        >
          {saveLoading ? '⏳ Salvando...' : 'Salvar no histórico'}
        </button>
      </div>

      <div className="method-info">
        <span className="method-dot" />
        <span>Método: {options.thresholdMode === 'auto' ? 'Otsu automático' : 'Adaptativo'}</span>
      </div>
    </div>
  );
};
