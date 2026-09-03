import React from 'react';
import {
  Sliders,
  Sparkles,
  GraduationCap,
  Split,
  Filter,
  Sparkle,
  Contrast,
  RotateCcw,
  BookmarkPlus,
  Play,
  Zap,
  Crop,
  Search,
  CheckCircle2,
} from 'lucide-react';
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

  const applyPreset = (preset: 'balanced' | 'sensitive' | 'denoise') => {
    if (preset === 'balanced') {
      onChange({
        sensitivity: 0.44,
        padding: 4,
        minLetterSize: 5,
        removeNoise: true,
        splitGroupedLetters: true,
        filterNonLetters: true,
      });
    } else if (preset === 'sensitive') {
      onChange({
        sensitivity: 0.58,
        padding: 5,
        minLetterSize: 3,
        removeNoise: false,
        splitGroupedLetters: true,
        filterNonLetters: true,
      });
    } else if (preset === 'denoise') {
      onChange({
        sensitivity: 0.35,
        padding: 3,
        minLetterSize: 8,
        removeNoise: true,
        splitGroupedLetters: true,
        filterNonLetters: true,
      });
    }
  };

  const configCards = [
    {
      key: 'sensitivity',
      icon: <Zap size={15} />,
      label: 'Sensibilidade',
      description: 'Define a sensibilidade de detecção dos traços.',
      hint: 'Valores altos detectam traços sutis com risco de ruído.',
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
          aria-label="Sensibilidade de detecção"
        />
      ),
    },
    {
      key: 'padding',
      icon: <Crop size={15} />,
      label: 'Margem do recorte',
      description: 'Espaço de respiro em torno de cada caractere.',
      hint: 'Evita cortar extremidades de letras itálicas ou serifadas.',
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
          aria-label="Margem de recorte"
        />
      ),
    },
    {
      key: 'minLetterSize',
      icon: <Search size={15} />,
      label: 'Tamanho mínimo',
      description: 'Descarta áreas menores que o limiar estipulado.',
      hint: 'Filtra manchas minúsculas e artefatos de digitalização.',
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
          aria-label="Tamanho mínimo do caractere"
        />
      ),
    },
  ];

  return (
    <div className="control-panel">
      <div className="panel-header">
        <div className="panel-header-title">
          <Sliders size={18} className="panel-header-icon" />
          <div>
            <span className="eyebrow">Parâmetros de Visão</span>
            <h3>Configurações</h3>
          </div>
        </div>
        <span className="panel-badge">
          <span className="badge-dot" />
          Ativo
        </span>
      </div>

      {/* Quick Presets */}
      <div className="presets-section">
        <span className="section-label">Ajustes Rápidos (Presets):</span>
        <div className="presets-buttons">
          <button
            type="button"
            className="preset-pill"
            onClick={() => applyPreset('balanced')}
            title="Ajuste equilibrado para uso geral"
          >
            Equilibrado
          </button>
          <button
            type="button"
            className="preset-pill"
            onClick={() => applyPreset('sensitive')}
            title="Para letras fracas ou fontes finas"
          >
            Alta Sensib.
          </button>
          <button
            type="button"
            className="preset-pill"
            onClick={() => applyPreset('denoise')}
            title="Para imagens com ruído ou digitalização ruidosa"
          >
            Anti-Ruído
          </button>
        </div>
      </div>

      <div className="settings-stack">
        {configCards.map((setting) => (
          <div className="control-group" key={setting.key}>
            <div className="setting-topline">
              <div className="setting-title-wrap">
                <span className="setting-icon" aria-hidden="true">
                  {setting.icon}
                </span>
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

        {/* Mode Selector */}
        <div className="mode-selector-group">
          <label className="mode-selector-label">Motor de Processamento</label>
          <div className="mode-options-grid">
            <button
              type="button"
              className={`mode-btn ${options.mode !== 'academic' ? 'active' : ''}`}
              onClick={() => handleChange('mode', 'enhanced')}
            >
              <div className="mode-btn-header">
                <Sparkles size={16} className="mode-icon" />
                <span className="mode-btn-title">Modo Aprimorado</span>
              </div>
              <span className="mode-btn-desc">
                Segmentação com IA de precisão, separação de ligaduras e descarte de linhas.
              </span>
            </button>
            <button
              type="button"
              className={`mode-btn ${options.mode === 'academic' ? 'active' : ''}`}
              onClick={() => handleChange('mode', 'academic')}
            >
              <div className="mode-btn-header">
                <GraduationCap size={16} className="mode-icon" />
                <span className="mode-btn-title">Trabalho Acadêmico</span>
              </div>
              <span className="mode-btn-desc">
                Pipeline de 7 etapas da literatura acadêmica original de P.I.
              </span>
            </button>
          </div>
        </div>

        {/* Feature Toggles */}
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
                <span className="toggle-icon">
                  <Split size={14} />
                </span>
                <strong>Separar letras coladas</strong>
              </span>
              <small>Projeção vertical para quebra de caracteres adjacentes (kerning).</small>
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
                <span className="toggle-icon">
                  <Filter size={14} />
                </span>
                <strong>Filtrar não-letras</strong>
              </span>
              <small>Descarta linhas, sublinhados, molduras e artefatos geométricos.</small>
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
                <span className="toggle-icon">
                  <Sparkle size={14} />
                </span>
                <strong>Remover ruídos</strong>
              </span>
              <small>Aplica filtragem morfológica para limpar ruído sal-e-pimenta.</small>
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
                <span className="toggle-icon">
                  <Contrast size={14} />
                </span>
                <strong>Melhorar contraste</strong>
              </span>
              <small>Equalização CLAHE para ressaltar caracteres em fundos difíceis.</small>
            </span>
          </label>
        </div>
      </div>

      {/* Button Action Stack */}
      <div className="button-group button-group-stack">
        <button
          onClick={onSegment}
          disabled={loading || !hasImage}
          className="btn btn-primary btn-glow"
        >
          <Play size={16} fill="currentColor" />
          <span>{loading ? 'Processando Segmentação...' : 'Segmentar Imagem'}</span>
        </button>

        <div className="button-row">
          <button
            onClick={onReset}
            disabled={loading}
            className="btn btn-secondary"
            title="Limpar imagens e resultados atuais"
          >
            <RotateCcw size={15} />
            <span>Limpar</span>
          </button>

          <button
            onClick={onSave}
            disabled={saveLoading || loading || !hasResult}
            className="btn btn-secondary"
            title="Salvar resultado atual no histórico local"
          >
            <BookmarkPlus size={15} />
            <span>{saveLoading ? 'Salvando...' : 'Salvar'}</span>
          </button>
        </div>
      </div>

      <div className="method-info">
        <CheckCircle2 size={13} className="method-dot-icon" />
        <span>Binarização: {options.thresholdMode === 'auto' ? 'Otsu Global Automático' : 'Limiar Adaptativo Local'}</span>
      </div>
    </div>
  );
};

