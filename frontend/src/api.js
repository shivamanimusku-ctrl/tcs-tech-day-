/**
 * API client utility — all fetch calls to the backend.
 */

const API_BASE = 'http://localhost:8000/api';

async function fetchJSON(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchJSON('/dashboard/summary'),

  // Alerts
  getAlerts: (status) => fetchJSON(status ? `/alerts?status=${status}` : '/alerts'),
  updateAlertStatus: (alertId, status) =>
    fetchJSON(`/alerts/${alertId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
  escalateAlert: (alertId) =>
    fetchJSON(`/alerts/${alertId}/escalate`, { method: 'POST' }),
  regenerateAlerts: () => fetchJSON('/alerts/generate', { method: 'POST' }),

  // Data endpoints
  getMachines: () => fetchJSON('/machines'),
  getMachineReadings: (machineId) => fetchJSON(`/machines/${machineId}/readings`),
  getProduction: (lineId) => fetchJSON(lineId ? `/production?line_id=${lineId}` : '/production'),
  getQuality: (lineId) => fetchJSON(lineId ? `/quality?line_id=${lineId}` : '/quality'),
  getMaterials: (lineId) => fetchJSON(lineId ? `/materials?line_id=${lineId}` : '/materials'),
  getShifts: (lineId) => fetchJSON(lineId ? `/shifts?line_id=${lineId}` : '/shifts'),
  getNotes: (lineId) => fetchJSON(lineId ? `/notes?line_id=${lineId}` : '/notes'),
  getOrders: (lineId) => fetchJSON(lineId ? `/orders?line_id=${lineId}` : '/orders'),

  // Seed/reset
  reseed: () => fetchJSON('/seed', { method: 'POST' }),
};
