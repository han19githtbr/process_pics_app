import axios from 'axios';
import { ProcessingOptions, SegmentResult, ComparisonResult, HistoryEntry } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new Event('auth-expired'));
    }
    return Promise.reject(error);
  },
);

export const login = async (email: string, password: string): Promise<void> => {
  await apiClient.post('/auth/login', { email, password });
};

export const checkSession = async (): Promise<boolean> => {
  const response = await apiClient.get('/auth/session');
  return response.data?.authenticated === true;
};

export const segmentImage = async (
  image: string,
  options?: ProcessingOptions,
  fileName?: string
): Promise<SegmentResult> => {
  const response = await apiClient.post(
    '/segment',
    { image, fileName, options: options || {} },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data;
};

export const compareImages = async (
  sourceImage: string,
  comparisonImage: string,
  options?: ProcessingOptions
): Promise<ComparisonResult> => {
  const response = await apiClient.post(
    '/compare',
    { sourceImage, comparisonImage, options: options || {} },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data;
};

export const getProcessingHistory = async (): Promise<HistoryEntry[]> => {
  const response = await apiClient.get('/history');
  return response.data?.items ?? [];
};

export const searchProcessingHistory = async (query: string): Promise<HistoryEntry[]> => {
  const response = await apiClient.get('/history/search', {
    params: { q: query },
  });
  return response.data?.items ?? [];
};

export const saveProcessingResult = async (payload: {
  imageData?: string;
  sourceName?: string;
  transcript?: string;
  letters?: Array<Record<string, any>>;
  metadata?: Record<string, any>;
}): Promise<HistoryEntry | null> => {
  const response = await apiClient.post('/history/save', payload, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data ?? null;
};

export const getHistoryItem = async (itemId: string): Promise<HistoryEntry | null> => {
  const response = await apiClient.get(`/history/${itemId}`);
  return response.data ?? null;
};

export const deleteHistoryItem = async (itemId: string): Promise<boolean> => {
  const response = await apiClient.delete(`/history/${itemId}`);
  return response.status === 200;
};

export const clearProcessingHistory = async (): Promise<boolean> => {
  const response = await apiClient.delete('/history');
  return response.status === 200;
};
