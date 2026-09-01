export interface ProcessingOptions {
  thresholdMode?: 'auto' | 'adaptive';
  sensitivity?: number;
  padding?: number;
  minLetterSize?: number;
  maxLetterSize?: number;
  removeNoise?: boolean;
  enhanceContrast?: boolean;
  maxImageSize?: number;
}
