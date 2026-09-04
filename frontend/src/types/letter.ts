export interface LetterConfidenceDetails {
  aspect_ratio?: number;
  contrast?: number;
  line_coherence?: number;
  density?: number;
  overall?: number;
}

export interface Letter {
  id?: number;
  line?: number;
  x: number;
  y: number;
  width: number;
  height: number;
  area: number;
  confidence: number;
  confidenceDetails?: LetterConfidenceDetails;
  image?: string;
}