import { apiConfig } from "./config";

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiConfig.baseUrl}${path}`);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function postJson<TResponse, TBody>(
  path: string,
  body?: TBody,
): Promise<TResponse> {
  const res = await fetch(`${apiConfig.baseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status}`);
  }

  return (await res.json()) as TResponse;
}
