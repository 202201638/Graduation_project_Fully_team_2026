const runtimeConfig = globalThis as typeof globalThis & {
  __MEDISCAN_API_BASE_URL__?: string;
};

export const environment = {
  production: true,
  backendBaseUrl: runtimeConfig.__MEDISCAN_API_BASE_URL__ || '',
};
