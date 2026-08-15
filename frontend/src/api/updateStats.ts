import { apiClient } from "./client";


export interface UpdateStats {
  total: number;
  by_type: Record<string, number>;
}


export async function getUpdateStats(): Promise<UpdateStats> {

  const response =
    await apiClient.get<UpdateStats>(
      "/updates/stats",
    );

  return response.data;
}
