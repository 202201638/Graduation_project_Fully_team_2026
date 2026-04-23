const runtimeConfig = globalThis as typeof globalThis & {
  __MEDISCAN_API_BASE_URL__?: string;
};

export const environment = {
  production: false,
  backendBaseUrl: runtimeConfig.__MEDISCAN_API_BASE_URL__ || 'http://localhost:8000',
};
