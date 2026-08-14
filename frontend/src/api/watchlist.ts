import { apiClient } from "./client";
import type {
  WatchlistCreateRequest,
  WatchlistItem,
} from "../types/stock";

export async function getWatchlist(): Promise<
  WatchlistItem[]
> {
  const response = await apiClient.get<WatchlistItem[]>(
    "/watchlist",
  );

  return response.data;
}

export async function addToWatchlist(
  request: WatchlistCreateRequest,
): Promise<WatchlistItem> {
  const response = await apiClient.post<WatchlistItem>(
    "/watchlist",
    request,
  );

  return response.data;
}

export async function removeFromWatchlist(
  symbol: string,
): Promise<void> {
  await apiClient.delete(`/watchlist/${symbol}`);
}
