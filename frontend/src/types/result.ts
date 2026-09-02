import { Letter } from './letter';

export interface PipelineStep {
  step: number;
  title: string;
  technique: string;
  formula?: string;
  description: string;
  image: string;
}

export interface SegmentResult {
  letters: Letter[];
  debugImage?: string;
  transcript?: string;
  steps?: PipelineStep[];
  meta: {
    width: number;
    height: number;
    totalLetters: number;
    processingTime: number;
    confidenceScore: number;
    edgePixels?: number;
    splits_count?: number;
    filtered_count?: number;
    mode?: string;
    warnings?: string[];
    transcript?: string;
  };
  confidence?: number;
}

export interface HistoryEntry {
  _id?: string;
  imageData?: string;
  sourceName?: string;
  transcript?: string;
  createdAt?: string;
  letters?: Letter[];
  metadata?: {
    totalLetters?: number;
    confidenceScore?: number;
    processingTime?: number;
    transcript?: string;
  };
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
