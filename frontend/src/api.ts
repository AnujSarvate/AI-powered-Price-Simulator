const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export type Product = {
  product_id: string;
  sku: string;
  name: string;
  unit_cost: number;
  list_price: number;
  category: string;
  elasticity: number;
  q0: number;
};

export type SimulationRun = {
  run_id: string;
  scenario_id: string;
  mode: string;
  total_profit: number;
  series: Record<
    string,
    Array<{
      week_index: number;
      price: number;
      quantity: number;
      gross_profit: number;
    }>
  >;
};

export const api = {
  health: () => request<{ status: string }>("/v1/health"),
  listProducts: () => request<Product[]>("/v1/products"),
  createProduct: (body: Omit<Product, "product_id">) =>
    request<Product>("/v1/products", { method: "POST", body: JSON.stringify(body) }),
  createScenario: (body: {
    name: string;
    horizon_weeks: number;
    product_ids: string[];
  }) => request<{ scenario_id: string }>("/v1/scenarios", { method: "POST", body: JSON.stringify(body) }),
