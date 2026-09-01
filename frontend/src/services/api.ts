import axios from 'axios';
import { ProcessingOptions, SegmentResult, ComparisonResult } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const segmentImage = async (
  image: string,
  options?: ProcessingOptions
): Promise<SegmentResult> => {
  const response = await axios.post(
    `${API_URL}/segment`,
    { image, options: options || {} },
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
  const response = await axios.post(
    `${API_URL}/compare`,
    { sourceImage, comparisonImage, options: options || {} },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data;
};
