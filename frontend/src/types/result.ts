import { Letter } from './letter';

export interface PipelineStep {
  step: number;
  title: string;
  technique: string;
  formula?: string;
  description: string;
  image: string;
}

export interface ConfidenceBreakdown {
  overall: number;
  letter_average?: number;
  aspect_ratio_score?: number;
  contrast_score?: number;
  line_coherence_score?: number;
  density_score?: number;
  weights?: {
    aspect_ratio: number;
    contrast: number;
    line_coherence: number;
    density: number;
  };
  evaluated_letters?: number;
  description?: string;
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
    confidenceBreakdown?: ConfidenceBreakdown;
    edgePixels?: number;
    splits_count?: number;
    splitsCount?: number;
    filtered_count?: number;
    filteredCount?: number;
    mode?: string;
    warnings?: string[];
    transcript?: string;
  };
  confidence?: number;
  confidenceBreakdown?: ConfidenceBreakdown;
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
