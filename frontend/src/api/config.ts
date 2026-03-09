export const apiConfig = {
  useMock: import.meta.env.VITE_USE_MOCK === "true",
  baseUrl: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
};
