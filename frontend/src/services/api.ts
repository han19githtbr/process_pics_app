import axios from 'axios';
import { ProcessingOptions, SegmentResult, ComparisonResult, HistoryEntry } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const requestConfig = { withCredentials: true };

export const login = async (email: string, password: string): Promise<void> => {
  await axios.post(`${API_URL}/auth/login`, { email, password }, requestConfig);
};

export const checkSession = async (): Promise<boolean> => {
  const response = await axios.get(`${API_URL}/auth/session`, requestConfig);
  return response.data?.authenticated === true;
};

export const segmentImage = async (
  image: string,
  options?: ProcessingOptions,
  fileName?: string
): Promise<SegmentResult> => {
  const response = await axios.post(
    `${API_URL}/segment`,
    { image, fileName, options: options || {} },
    {
      ...requestConfig,
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
  const response = await axios.post(
    `${API_URL}/compare`,
    { sourceImage, comparisonImage, options: options || {} },
    {
      ...requestConfig,
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data;
};

export const getProcessingHistory = async (): Promise<HistoryEntry[]> => {
  const response = await axios.get(`${API_URL}/history`, requestConfig);
  return response.data?.items ?? [];
};

export const searchProcessingHistory = async (query: string): Promise<HistoryEntry[]> => {
  const response = await axios.get(`${API_URL}/history/search`, {
    params: { q: query }, ...requestConfig,
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
  const response = await axios.post(`${API_URL}/history/save`, payload, {
    ...requestConfig,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data ?? null;
};

export const getHistoryItem = async (itemId: string): Promise<HistoryEntry | null> => {
  const response = await axios.get(`${API_URL}/history/${itemId}`, requestConfig);
  return response.data ?? null;
};

export const deleteHistoryItem = async (itemId: string): Promise<boolean> => {
  const response = await axios.delete(`${API_URL}/history/${itemId}`, requestConfig);
  return response.status === 200;
};

export const clearProcessingHistory = async (): Promise<boolean> => {
  const response = await axios.delete(`${API_URL}/history`, requestConfig);
  return response.status === 200;
};
