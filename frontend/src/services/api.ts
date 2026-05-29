import axios from 'axios'
import type {
  Campaign,
  ForecastResult,
  Hospital,
  Department,
  InventorySummary,
  WastageAnalysis,
  BloodType,
  ForecastHorizon,
  WastageReason,
} from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// ── Hospitals ────────────────────────────────────────────────────────────────

export const hospitalApi = {
  list: () => api.get<Hospital[]>('/hospitals/').then(r => r.data),
  get: (id: string) => api.get<Hospital>(`/hospitals/${id}`).then(r => r.data),
  create: (payload: Omit<Hospital, 'id' | 'created_at'>) =>
    api.post<Hospital>('/hospitals/', payload).then(r => r.data),
  delete: (id: string) => api.delete(`/hospitals/${id}`),
  getDepartments: (hospitalId: string) =>
    api.get<Department[]>(`/hospitals/${hospitalId}/departments`).then(r => r.data),
  createDepartment: (hospitalId: string, payload: { name: string; code: string }) =>
    api.post<Department>(`/hospitals/${hospitalId}/departments`, payload).then(r => r.data),
}

// ── Inventory ────────────────────────────────────────────────────────────────

export const inventoryApi = {
  getSummary: (hospitalId: string) =>
    api.get<InventorySummary>(`/hospitals/${hospitalId}/inventory/summary`).then(r => r.data),
  addUnits: (hospitalId: string, payload: { blood_type: BloodType; units_available: number; expiry_date: string }) =>
    api.post(`/hospitals/${hospitalId}/inventory/units`, payload).then(r => r.data),
  consumeBlood: (hospitalId: string, payload: { department_id: string; blood_type: BloodType; units: number; consumption_date: string }) =>
    api.post(`/hospitals/${hospitalId}/inventory/consume`, payload).then(r => r.data),
  recordWastage: (hospitalId: string, payload: { blood_type: BloodType; units_wasted: number; reason: WastageReason; wastage_date: string; notes?: string }) =>
    api.post(`/hospitals/${hospitalId}/inventory/wastage`, payload).then(r => r.data),
  getWastageAnalysis: (hospitalId: string, startDate: string, endDate: string) =>
    api.get<WastageAnalysis>(`/hospitals/${hospitalId}/inventory/wastage/analysis`, {
      params: { start_date: startDate, end_date: endDate },
    }).then(r => r.data),
  getExpiringUnits: (hospitalId: string, days = 3) =>
    api.get(`/hospitals/${hospitalId}/inventory/expiring`, { params: { days } }).then(r => r.data),
}

// ── Forecasting ──────────────────────────────────────────────────────────────

export const forecastApi = {
  run: (hospitalId: string, payload: { blood_type: BloodType; horizon: ForecastHorizon; department_id?: string }) =>
    api.post<ForecastResult[]>(`/hospitals/${hospitalId}/forecasts/run`, payload).then(r => r.data),
  get: (hospitalId: string, bloodType: BloodType, horizon: ForecastHorizon) =>
    api.get<ForecastResult[]>(`/hospitals/${hospitalId}/forecasts/`, {
      params: { blood_type: bloodType, horizon },
    }).then(r => r.data),
}

// ── Campaigns ────────────────────────────────────────────────────────────────

export const campaignApi = {
  listActive: () => api.get<Campaign[]>('/campaigns/').then(r => r.data),
  listByHospital: (hospitalId: string) =>
    api.get<Campaign[]>(`/campaigns/hospitals/${hospitalId}`).then(r => r.data),
  create: (hospitalId: string, payload: Omit<Campaign, 'id' | 'hospital_id' | 'collected_units' | 'progress_percentage' | 'status' | 'created_at' | 'updated_at'>) =>
    api.post<Campaign>(`/campaigns/hospitals/${hospitalId}`, payload).then(r => r.data),
  activate: (id: string) => api.post<Campaign>(`/campaigns/${id}/activate`).then(r => r.data),
  donate: (id: string, units: number) =>
    api.post<Campaign>(`/campaigns/${id}/donate`, { units }).then(r => r.data),
  cancel: (id: string) => api.post<Campaign>(`/campaigns/${id}/cancel`).then(r => r.data),
}

export default api
