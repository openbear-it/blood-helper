export type BloodType = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-'
export type InventoryStatus = 'adequate' | 'low' | 'critical' | 'surplus'
export type CampaignStatus = 'draft' | 'active' | 'completed' | 'cancelled'
export type ForecastHorizon = 'daily' | 'weekly' | 'monthly'
export type WastageReason = 'expired' | 'contaminated' | 'administrative' | 'other'

export interface Hospital {
  id: string
  name: string
  code: string
  city: string
  region: string
  capacity_beds: number
  created_at: string
}

export interface Department {
  id: string
  hospital_id: string
  name: string
  code: string
  created_at: string
}

export interface BloodUnit {
  id: string
  hospital_id: string
  blood_type: BloodType
  units_available: number
  units_reserved: number
  units_usable: number
  expiry_date: string
  status: InventoryStatus
  last_updated: string
}

export interface InventorySummary {
  hospital_id: string
  blood_types: Record<string, { available: number; reserved: number; expiring_soon: number }>
  critical_types: string[]
}

export interface ConsumptionRecord {
  id: string
  hospital_id: string
  department_id: string
  blood_type: BloodType
  units_consumed: number
  consumption_date: string
  created_at: string
}

export interface WastageRecord {
  id: string
  hospital_id: string
  blood_type: BloodType
  units_wasted: number
  reason: WastageReason
  wastage_date: string
  notes: string
  estimated_cost: number
  created_at: string
}

export interface WastageAnalysis {
  period: { start: string; end: string }
  total_units_wasted: number
  total_estimated_cost: number
  by_blood_type: Record<string, { units: number; cost: number }>
  by_reason: Record<string, number>
}

export interface ForecastResult {
  id: string
  hospital_id: string
  department_id: string | null
  blood_type: BloodType
  horizon: ForecastHorizon
  forecast_date: string
  predicted_units: number
  lower_bound: number
  upper_bound: number
  model_name: string
  confidence: number
  created_at: string
}

export interface Campaign {
  id: string
  hospital_id: string
  title: string
  description: string
  target_blood_types: BloodType[]
  target_units: number
  collected_units: number
  progress_percentage: number
  start_date: string
  end_date: string
  status: CampaignStatus
  created_at: string
  updated_at: string
}
