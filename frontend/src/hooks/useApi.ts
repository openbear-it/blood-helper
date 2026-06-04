import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hospitalApi, inventoryApi, forecastApi, campaignApi } from '@/services/api'
import type { BloodType, ForecastHorizon, ScenarioMethod, WastageReason } from '@/types'

// ── Hospital Hooks ────────────────────────────────────────────────────────────

export function useHospitals() {
  return useQuery({
    queryKey: ['hospitals'],
    queryFn: hospitalApi.list,
  })
}

export function useHospital(id: string) {
  return useQuery({
    queryKey: ['hospitals', id],
    queryFn: () => hospitalApi.get(id),
    enabled: !!id,
  })
}

export function useDepartments(hospitalId: string) {
  return useQuery({
    queryKey: ['departments', hospitalId],
    queryFn: () => hospitalApi.getDepartments(hospitalId),
    enabled: !!hospitalId,
  })
}

// ── Inventory Hooks ──────────────────────────────────────────────────────────

export function useInventorySummary(hospitalId: string) {
  return useQuery({
    queryKey: ['inventory', 'summary', hospitalId],
    queryFn: () => inventoryApi.getSummary(hospitalId),
    enabled: !!hospitalId,
    refetchInterval: 30_000,
  })
}

export function useWastageAnalysis(hospitalId: string, startDate: string, endDate: string) {
  return useQuery({
    queryKey: ['wastage', 'analysis', hospitalId, startDate, endDate],
    queryFn: () => inventoryApi.getWastageAnalysis(hospitalId, startDate, endDate),
    enabled: !!hospitalId && !!startDate && !!endDate,
  })
}

export function useAddBloodUnits(hospitalId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: { blood_type: BloodType; units_available: number; expiry_date: string }) =>
      inventoryApi.addUnits(hospitalId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inventory', 'summary', hospitalId] })
    },
  })
}

export function useConsumeBlood(hospitalId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: { department_id: string; blood_type: BloodType; units: number; consumption_date: string }) =>
      inventoryApi.consumeBlood(hospitalId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inventory', 'summary', hospitalId] })
    },
  })
}

export function useRecordWastage(hospitalId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: { blood_type: BloodType; units_wasted: number; reason: WastageReason; wastage_date: string; notes?: string }) =>
      inventoryApi.recordWastage(hospitalId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wastage', 'analysis', hospitalId] })
    },
  })
}

// ── Forecast Hooks ───────────────────────────────────────────────────────────

export function useForecasts(hospitalId: string, bloodType: BloodType, horizon: ForecastHorizon) {
  return useQuery({
    queryKey: ['forecasts', hospitalId, bloodType, horizon],
    queryFn: () => forecastApi.get(hospitalId, bloodType, horizon),
    enabled: !!hospitalId,
  })
}

export function useRunForecast(hospitalId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: { blood_type: BloodType; horizon: ForecastHorizon; department_id?: string }) =>
      forecastApi.run(hospitalId, payload),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({
        queryKey: ['forecasts', hospitalId, variables.blood_type, variables.horizon],
      })
    },
  })
}

// ── Campaign Hooks ───────────────────────────────────────────────────────────

export function useActiveCampaigns() {
  return useQuery({
    queryKey: ['campaigns', 'active'],
    queryFn: campaignApi.listActive,
    refetchInterval: 60_000,
  })
}

export function useHospitalCampaigns(hospitalId: string) {
  return useQuery({
    queryKey: ['campaigns', 'hospital', hospitalId],
    queryFn: () => campaignApi.listByHospital(hospitalId),
    enabled: !!hospitalId,
  })
}

export function useDonateToMutation(campaignId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (units: number) => campaignApi.donate(campaignId, units),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['campaigns'] })
    },
  })
}

// ── PSI Hooks ────────────────────────────────────────────────────────────────

export function usePSI(
  hospitalId: string,
  params?: { horizon_days?: number; percentile?: number; method?: ScenarioMethod; history_days?: number; friction?: number }
) {
  return useQuery({
    queryKey: ['psi', hospitalId, params],
    queryFn: () => inventoryApi.getPSI(hospitalId, params),
    enabled: !!hospitalId,
    refetchInterval: 60_000,
  })
}

export function useInventoryHistory(
  hospitalId: string,
  startDate: string,
  endDate: string,
  bloodType?: string,
) {
  return useQuery({
    queryKey: ['inventory', 'history', hospitalId, startDate, endDate, bloodType],
    queryFn: () => inventoryApi.getHistory(hospitalId, startDate, endDate, bloodType),
    enabled: !!hospitalId && !!startDate && !!endDate,
  })
}
