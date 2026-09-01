import { useState, useCallback } from 'react';
import { SegmentResult, ProcessingOptions } from '../types';
import { segmentImage } from '../services/api';

export const useSegmenter = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SegmentResult | null>(null);

  const segment = useCallback(
    async (image: string, options?: ProcessingOptions, fileName?: string) => {
      setLoading(true);
      setError(null);

      try {
        const data = await segmentImage(image, options, fileName);

        const normalizedResult = {
          ...data,
          letters: [...(data.letters ?? [])],
        };

        setResult(normalizedResult);
        return normalizedResult;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro ao segmentar';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setLoading(false);
  }, []);

  return { loading, error, result, segment, reset };
};
