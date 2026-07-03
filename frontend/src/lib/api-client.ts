const isDev = import.meta.env.DEV;

function getConfiguredApiUrl(): string | undefined {
  const url = import.meta.env.VITE_API_BASE_URL;
  return url && url.length > 0 ? url.replace(/\/$/, "") : undefined;
}

export function getApiBaseUrl(): string {
  if (isDev) {
    return "";
  }
  return getConfiguredApiUrl() ?? window.location.origin;
}

export function getSocketUrl(): string {
  if (isDev) {
    return window.location.origin;
  }
  return getConfiguredApiUrl() ?? window.location.origin;
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = baseUrl ? `${baseUrl}${path}` : path;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),

  post: <T>(path: string, data?: unknown) =>
    apiFetch<T>(path, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),
};
