import { apiClient } from "./client";

import type {
  Stock,
} from "../types/stock";


export interface Subscription {
  id: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  stock: Stock;
}


export interface SubscribeRequest {
  symbol: string;
  company_name?: string;
  exchange?: string;
  sector?: string | null;
}


export async function getSubscriptions(): Promise<
  Subscription[]
> {
  const response =
    await apiClient.get<Subscription[]>(
      "/subscriptions",
    );

  return response.data;
}


export async function subscribe(
  request: SubscribeRequest,
): Promise<Subscription> {

  const response =
    await apiClient.post<Subscription>(
      "/subscriptions",
      request,
    );

  return response.data;
}


export async function unsubscribe(
  symbol: string,
): Promise<void> {

  await apiClient.delete(
    `/subscriptions/${symbol}`,
  );
}
