import { apiClient } from "./client";

export interface SectorIndex {
  key: string;
  name: string;
  symbol: string;
}

export interface SectorHistoryPoint {
  date: string;
  value: number;
  close: number;
}

export interface SectorConstituent {
  symbol: string;
  company_name: string;
  price: number | null;
  change_percent: number | null;
  volume: number | string | null;
}

export interface SectorAnalysisResponse {
  key: string;
  name: string;
  period: string;
  sector_return_percent: number | null;
  nifty50_return_percent: number | null;
  excess_return_percent: number | null;
  sector_history: SectorHistoryPoint[];
  nifty50_history: SectorHistoryPoint[];
  constituent_histories: Record<string, SectorHistoryPoint[]>;
  constituents: SectorConstituent[];
  constituents_error: string | null;
  updated_at: string;
}

export async function getSectorIndices(): Promise<SectorIndex[]> {
  const response = await apiClient.get<SectorIndex[]>("/market/sectors");
  return response.data;
}

export async function getSectorAnalysis(
  sectorKey: string,
  period: string,
  symbols: string[] = [],
): Promise<SectorAnalysisResponse> {
  const response = await apiClient.get<SectorAnalysisResponse>(
    `/market/sectors/${encodeURIComponent(sectorKey)}`,
    { params: { period, ...(symbols.length ? { symbols: symbols.join(",") } : {}) } },
  );
  return response.data;
}
