export interface ProcessingOptions {
  thresholdMode?: 'auto' | 'adaptive';
  sensitivity?: number;
  padding?: number;
  minLetterSize?: number;
  maxLetterSize?: number;
  removeNoise?: boolean;
  enhanceContrast?: boolean;
  maxImageSize?: number;
  mode?: 'enhanced' | 'academic';
  splitGroupedLetters?: boolean;
  filterNonLetters?: boolean;
  filterBackgroundNoise?: boolean;
  cannyLow?: number;
  cannyHigh?: number;
  bilateralD?: number;
  bilateralSigmaColor?: number;
  bilateralSigmaSpace?: number;
}
