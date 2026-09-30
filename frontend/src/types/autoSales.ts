export interface AutoSales {
  id: number;
  symbol: string;
  company_name: string;
  segment: string;
  month: string;
  registrations: number | null;
  domestic_sales: number | null;
  export_sales: number | null;
  total_sales: number | null;
  yoy_growth: number | null;
  mom_growth: number | null;
  market_share: number | null;
  data_type: string;
  source: string;
  source_url: string | null;
  is_projected: boolean;
}
