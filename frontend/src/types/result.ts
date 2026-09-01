import { Letter } from './letter';

export interface SegmentResult {
  letters: Letter[];
  debugImage: string;
  transcript?: string;
  meta: {
    width: number;
    height: number;
    totalLetters: number;
    processingTime: number;
    confidenceScore: number;
  };
  confidence: number;
}

export interface ComparisonResult {
  sourceLetters?: number;
  targetLetters?: number;
  similarity?: number;
  status?: string;
  verdict?: string;
  threshold?: {
    plagio: number;
    aceita: number;
  };
  sourceTranscript?: string;
  targetTranscript?: string;
}
