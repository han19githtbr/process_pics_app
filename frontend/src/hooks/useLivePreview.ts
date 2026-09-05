import { useEffect, useRef, useState } from 'react';
import { ProcessingOptions, SegmentResult } from '../types';
import { segmentImage } from '../services/api';

const DEBOUNCE_MS = 450;

/**
 * Roda a segmentação em segundo plano (com debounce) sempre que a imagem
 * carregada ou os parâmetros de processamento mudam, para que o usuário
 * veja o efeito de cada ajuste (Sensibilidade, Margem do recorte, etc.)
 * refletido ao vivo na imagem, sem precisar clicar em "Segmentar Imagem".
 *
 * Requisições antigas que ainda estejam "voando" quando um novo ajuste
 * chega são descartadas (via requestIdRef) para nunca sobrescrever o
 * preview com um resultado desatualizado.
 */
export const useLivePreview = (
  image: string | null,
  fileName: string | undefined,
  options: ProcessingOptions
) => {
  const [preview, setPreview] = useState<SegmentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const requestIdRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionsKey = JSON.stringify(options);

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    if (!image) {
      requestIdRef.current += 1;
      setPreview(null);
      setLoading(false);
      return;
    }

    const requestId = ++requestIdRef.current;
    setLoading(true);

    timeoutRef.current = setTimeout(() => {
      // `preview: true` garante que o backend NUNCA grave esta chamada no
      // histórico/MongoDB — só o botão "Segmentar Imagem" persiste dados.
      segmentImage(image, options, fileName, true)
        .then((data) => {
          if (requestIdRef.current === requestId) {
            setPreview(data);
          }
        })
        .catch(() => {
          if (requestIdRef.current === requestId) {
            setPreview(null);
          }
        })
        .finally(() => {
          if (requestIdRef.current === requestId) {
            setLoading(false);
          }
        });
    }, DEBOUNCE_MS);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [image, fileName, optionsKey]);

  return { preview, loading };
};
