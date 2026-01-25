const API_BASE = '/api'

interface HealthStatus {
  status: string
  services: {
    postgres: string
    opensearch: string
    redis: string
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`)
  }

  return response.json()
}

export const apiClient = {
  getHealth: (): Promise<HealthStatus> => {
    return fetchJson<HealthStatus>(`${API_BASE}/health`)
  },

  // Placeholder methods for future phases
  // uploadVideo: (file: File) => { ... }
  // search: (query: string) => { ... }
  // getVideo: (id: string) => { ... }
}
