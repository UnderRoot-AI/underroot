export interface CropRecommendation { crop: string; suitability: number; reason: string; season?: string; expected_duration_days?: number; model?: string; }
export interface FertilizerRecommendation { name: string; type?: "organic" | "inorganic" | string; quantity?: string; frequency?: string; reason: string; precautions?: string[]; confidence?: number; }
