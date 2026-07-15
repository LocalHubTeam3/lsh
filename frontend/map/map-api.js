/**
 * 지도 전용 API 어댑터입니다.
 * 실제 frontend 이식 시 아래 값을 VITE_API_BASE_URL 같은 환경변수로 교체하세요.
 */
const MAP_API_BASE_URL = window.LOCALHUB_API_BASE_URL || "http://localhost:8000";

window.localHubMapApi = {
  async getLocations(contentType) {
    const params = new URLSearchParams({ content_type: contentType });
    const response = await fetch(`${MAP_API_BASE_URL}/api/map/locations?${params}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`지도 API 요청 실패 (${response.status})`);
    return response.json();
  },

  async searchLocations(query, limit = 50) {
    const params = new URLSearchParams({ query, limit: String(limit) });
    const response = await fetch(`${MAP_API_BASE_URL}/api/map/search?${params}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`장소 검색 요청 실패 (${response.status})`);
    return response.json();
  },

  async getCrowd(locationId) {
    const response = await fetch(`${MAP_API_BASE_URL}/api/locations/${locationId}/crowd`, {
      headers: { Accept: "application/json" },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(body.detail || `혼잡도 API 요청 실패 (${response.status})`);
      error.status = response.status;
      throw error;
    }
    return body;
  },
};
