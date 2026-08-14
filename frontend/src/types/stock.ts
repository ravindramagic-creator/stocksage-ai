export interface Stock {
  id: number;
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string | null;
}

export interface WatchlistItem {
  id: number;
  stock: Stock;
}

export interface WatchlistCreateRequest {
  symbol: string;
}
