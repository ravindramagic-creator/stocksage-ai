import type { AutoSales } from "../types/autoSales";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface AutoSalesFilters {
  symbol?: string;
  segment?: string;
  startMonth?: string;
  endMonth?: string;
}

export async function fetchAutoSales(
  filters: AutoSalesFilters = {},
): Promise<AutoSales[]> {
  const params = new URLSearchParams();

  if (filters.symbol) params.set("symbol", filters.symbol);
  if (filters.segment) params.set("segment", filters.segment);
  if (filters.startMonth) params.set("start_month", `${filters.startMonth}-01`);
  if (filters.endMonth) params.set("end_month", `${filters.endMonth}-01`);

  const response = await fetch(
    `${API_BASE_URL}/auto-sales?${params.toString()}`,
  );

  if (!response.ok) {
    throw new Error(`Auto-sales request failed: ${response.status}`);
  }

  return response.json();
}
