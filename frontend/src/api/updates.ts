import { apiClient } from "./client";

export interface UpdateEvent {
  id: number;

  symbol: string;

  event_type: string;

  priority: string;

  title: string;

  description: string | null;

  source: string | null;

  source_url: string | null;

  old_value: number | null;

  new_value: number | null;

  event_time: string;

  created_at: string;
}


export interface GetUpdatesParams {
  symbol?: string;
  eventType?: string;
  priority?: string;
  limit?: number;
}


export async function getUpdates(
  params: GetUpdatesParams = {},
): Promise<UpdateEvent[]> {

  const searchParams =
    new URLSearchParams();


  if (params.symbol) {
    searchParams.set(
      "symbol",
      params.symbol,
    );
  }


  if (params.eventType) {
    searchParams.set(
      "event_type",
      params.eventType,
    );
  }


  if (params.priority) {
    searchParams.set(
      "priority",
      params.priority,
    );
  }


  searchParams.set(
    "limit",
    String(params.limit ?? 50),
  );


  const query =
    searchParams.toString();


  const url =
    query.length > 0
      ? `/updates?${query}`
      : "/updates";


  const response =
    await apiClient.get<UpdateEvent[]>(
      url,
    );


  return response.data;
}
