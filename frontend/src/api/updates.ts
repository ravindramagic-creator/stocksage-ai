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


export async function getUpdates(
  symbol?: string,
  limit = 50,
): Promise<UpdateEvent[]> {

  const response =
    await apiClient.get<UpdateEvent[]>(
      "/updates",
      {
        params: {
          ...(symbol
            ? { symbol }
            : {}),
          limit,
        },
      },
    );

  return response.data;
}
