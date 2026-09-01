import { useState, useCallback } from 'react';

export const useImageUpload = () => {
  const [image, setImage] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadImage = useCallback((file: File) => {
    // Validar tipo de arquivo
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setError('Formato de arquivo inválido. Use PNG, JPG ou JPEG.');
      return;
    }

    // Validar tamanho (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Arquivo muito grande. Máximo 10MB.');
      return;
    }

    setFile(file);
    setError(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      setImage(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  }, []);

  const resetImage = useCallback(() => {
    setImage(null);
    setFile(null);
    setError(null);
  }, []);

  return { image, file, error, uploadImage, resetImage };
};