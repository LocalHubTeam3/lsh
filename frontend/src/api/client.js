const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function request(path, options = {}) {
  const headers = { Accept: 'application/json', ...options.headers }
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  } catch {
    throw new ApiError('서버에 연결할 수 없습니다. FastAPI 서버를 확인해 주세요.', 0)
  }

  if (response.status === 204) return null
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).join(', ')
      : body.detail
    throw new ApiError(detail || `요청을 처리하지 못했습니다. (${response.status})`, response.status)
  }
  return body
}

export function toQuery(params) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, String(value))
  })
  return query.toString()
}
