// frontend/src/components/ImageBank/ImageBank.tsx
import React, { useCallback, useEffect, useState } from 'react';
import { RotateCw, Search, X, Trash2, ArrowRight } from 'lucide-react';
import { ImageBankEntry } from '../../types';
import { getImageBank, searchImageBank, deleteImageBankItem, clearImageBank } from '../../services/api';

type ImageBankProps = {
  /** Incremente este número para forçar um recarregamento (ex.: após salvar uma nova imagem) */
  refreshSignal?: number;
};

export const ImageBank: React.FC<ImageBankProps> = ({ refreshSignal }) => {
  const [items, setItems] = useState<ImageBankEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selected, setSelected] = useState<ImageBankEntry | null>(null);

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getImageBank();
      setItems(data);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const runSearch = useCallback(async (query: string) => {
    setLoading(true);
    try {
      const data = await searchImageBank(query);
      setItems(data);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshSignal]);

  useEffect(() => {
    const query = searchQuery.trim();
    if (!query) {
      void loadItems();
      return;
    }
    const debounce = setTimeout(() => void runSearch(query), 350);
    return () => clearTimeout(debounce);
  }, [searchQuery, loadItems, runSearch]);

  const handleRefresh = () => {
    const query = searchQuery.trim();
    if (query) void runSearch(query);
    else void loadItems();
  };

  const handleDelete = async (itemId: string, itemName?: string) => {
    const name = itemName || 'esta imagem';
    if (!window.confirm(`Tem certeza que deseja apagar "${name}" do Banco de Imagens de Alta Qualidade?`)) return;

    setDeletingId(itemId);
    try {
      await deleteImageBankItem(itemId);
      if (selected?._id === itemId) setSelected(null);
      handleRefresh();
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Não foi possível excluir o item do banco.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!items.length) return;
    if (
      !window.confirm(
        'Tem certeza que deseja apagar TODO o Banco de Imagens de Alta Qualidade? Todas as imagens salvas serão excluídas definitivamente.'
      )
    ) {
      return;
    }

    setClearing(true);
    try {
      await clearImageBank();
      setItems([]);
      setSelected(null);
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Não foi possível limpar o banco.');
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="history-panel">
      <div className="history-header">
        <div className="history-title-wrap">
          <h3>Imagens Salvas</h3>
          {items.length > 0 && <span className="history-count-badge">{items.length}</span>}
        </div>

        <div className="history-header-actions">
          {items.length > 0 && (
            <button
              type="button"
              className="history-clear-all-btn"
              onClick={() => void handleClearAll()}
              disabled={clearing || loading}
              title="Apagar todas as imagens do banco de alta qualidade"
              aria-label="Limpar todo o banco de imagens"
            >
              <Trash2 size={13} />
              <span>{clearing ? 'Limpando...' : 'Limpar Banco'}</span>
            </button>
          )}

          <button
            type="button"
            className={`history-refresh ${loading ? 'loading' : ''}`}
            onClick={handleRefresh}
            title="Recarregar banco de imagens"
          >
            <RotateCw size={13} className={loading ? 'spin-icon' : ''} />
            <span>{loading ? 'Atualizando...' : 'Atualizar'}</span>
          </button>
        </div>
      </div>

      <div className={`history-search ${searchQuery ? 'has-value' : ''}`}>
        <Search size={15} className="history-search-icon" />
        <input
          type="text"
          className="history-search-input"
          placeholder="Buscar por nome do arquivo salvo..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label="Buscar imagens no banco de alta qualidade"
        />
        {searchQuery && (
          <button
            type="button"
            className="history-search-clear"
            onClick={() => setSearchQuery('')}
            aria-label="Limpar busca"
          >
            <X size={12} />
          </button>
        )}
      </div>

      <div className="history-list">
        {items.length === 0 && !searchQuery.trim() ? (
          <div className="history-empty">
            <p>Nenhuma imagem salva no banco de alta qualidade até o momento.</p>
            <small>Clique em "Melhorar Qualidade da Imagem" acima para gerar e salvar a primeira.</small>
          </div>
        ) : (
          items.map((entry, index) => (
            <div
              key={entry._id ?? `${entry.sourceName}-${index}`}
              role="button"
              tabIndex={0}
              className="history-item"
              style={{ animationDelay: `${index * 35}ms` }}
              onClick={() => setSelected(entry)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setSelected(entry);
                }
              }}
            >
              <div className="history-item-top">
                {(entry.enhancedImage || entry.originalImage) && (
                  <img
                    src={entry.enhancedImage || entry.originalImage}
                    alt={entry.sourceName ?? 'Imagem melhorada'}
                    className="history-thumb"
                  />
                )}
                <div className="history-item-info">
                  <div className="history-item-info-top">
                    <span className="history-name">{entry.sourceName ?? 'Imagem melhorada'}</span>
                    <button
                      type="button"
                      className={`history-delete-item-btn ${deletingId === entry._id ? 'loading' : ''}`}
                      disabled={deletingId === entry._id}
                      onClick={(e) => {
                        e.stopPropagation();
                        void handleDelete(entry._id ?? '', entry.sourceName);
                      }}
                      title="Excluir esta imagem do banco de alta qualidade"
                      aria-label={`Excluir ${entry.sourceName ?? 'imagem'} do banco`}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                  <span className="history-meta">
                    {entry.createdAt ? new Date(entry.createdAt).toLocaleString('pt-BR') : 'Hoje'}
                  </span>
                  {entry.techniques && entry.techniques.length > 0 && (
                    <span className="history-letters-count">{entry.techniques.length} técnicas aplicadas</span>
                  )}
                </div>
              </div>

              <div className="history-item-footer">
                <span className="history-view-hint">
                  Ver Detalhes
                  <ArrowRight size={13} />
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {selected && (
        <div className="image-lightbox-backdrop" onClick={() => setSelected(null)}>
          <div className="image-lightbox-content" onClick={(e) => e.stopPropagation()}>
            <div className="lightbox-header">
              <h4>{selected.sourceName || 'Imagem de Alta Qualidade'}</h4>
              <button
                type="button"
                className="lightbox-close-btn"
                onClick={() => setSelected(null)}
                aria-label="Fechar ampliação"
              >
                <X size={18} />
              </button>
            </div>
            <div className="lightbox-img-wrapper">
              <img src={selected.enhancedImage || selected.originalImage} alt="Imagem de alta qualidade em detalhe" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
