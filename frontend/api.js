/**
 * LocalHub API adapter.
 * 실제 frontend로 이식할 때 API_BASE_URL만 환경변수 값으로 교체하면 됩니다.
 * 예: const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
 */
const API_BASE_URL = window.LOCALHUB_API_BASE_URL || "http://localhost:8000";

window.localHubApi = {
  async getLocations({ search = "", contentType = "", page = 1, size = 12 } = {}) {
    const params = new URLSearchParams({ page: String(page), size: String(size) });
    if (search.trim()) params.set("search", search.trim());
    if (contentType) params.set("content_type", contentType);

    const response = await fetch(`${API_BASE_URL}/api/locations?${params.toString()}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`장소 API 요청 실패 (${response.status})`);
    }
    return response.json();
  },
};
