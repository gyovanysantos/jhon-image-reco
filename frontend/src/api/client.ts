const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

export interface PartMatch {
  part_number: string;
  confidence_score: number;
  title: string;
  description: string;
  brand: string;
  mfg_number: string;
  url: string;
  specifications: Record<string, string>;
  pricing: string;
  catalog_page: string | number;
  datasheets: { title: string; url: string }[];
}

export interface RecognizeResponse {
  matches: PartMatch[];
}

export interface PartDetails {
  part_number: string;
  title: string;
  description: string;
  brand: string;
  mfg_number: string;
  url: string;
  specifications: Record<string, string>;
  pricing: string;
  catalog_page: string | number;
  image_keys: string[];
  datasheets: { title: string; url: string }[];
}

export async function recognizeImage(imageBase64: string): Promise<RecognizeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/recognize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: imageBase64 }),
  });

  if (!response.ok) {
    throw new Error(`Recognition failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getPartDetails(partNumber: string): Promise<PartDetails> {
  const response = await fetch(`${API_BASE_URL}/api/parts/${encodeURIComponent(partNumber)}`);

  if (!response.ok) {
    throw new Error(`Part lookup failed: ${response.statusText}`);
  }

  return response.json();
}
