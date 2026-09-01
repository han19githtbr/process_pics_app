export interface Letter {
  id?: number;
  line?: number;
  x: number;
  y: number;
  width: number;
  height: number;
  area: number;
  confidence: number;
  image?: string;
}