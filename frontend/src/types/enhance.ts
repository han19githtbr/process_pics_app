export interface EnhanceOptions {
  mode?: 'auto' | 'manual';
  denoiseStrength?: number;
  sharpenAmount?: number;
  claheClipLimit?: number;
  targetGlyphHeight?: number;
  maxUpscaleFactor?: number;
  maxDimension?: number;
}

export interface EnhancePipelineStep {
  step: number;
  title: string;
  technique: string;
  formula?: string;
  description: string;
  image: string;
}

export interface EnhanceMetrics {
  sharpnessBefore?: number;
  sharpnessAfter?: number;
  noiseBefore?: number;
  noiseAfter?: number;
  contrastBefore?: number;
  contrastAfter?: number;
  glyphHeightEstimate?: number;
  upscaleFactor?: number;
  denoiseH?: number;
  claheClipLimit?: number;
  sharpenAmount?: number;
  processingTime?: number;
  techniquesApplied?: string[];
  comparisonNote?: string;
}

export interface EnhanceResult {
  enhancedImage: string;
  originalImage: string;
  steps?: EnhancePipelineStep[];
  metrics: EnhanceMetrics;
  metadata?: {
    width?: number;
    height?: number;
    originalWidth?: number;
    originalHeight?: number;
    mode?: string;
  };
  savedToBank?: boolean;
  bankItemId?: string;
}

export interface ImageBankEntry {
  _id?: string;
  enhancedImage?: string;
  originalImage?: string;
  sourceName?: string;
  techniques?: string[];
  metrics?: EnhanceMetrics;
  createdAt?: string;
}
