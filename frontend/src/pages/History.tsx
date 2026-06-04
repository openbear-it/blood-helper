import { useState, useMemo } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  Stack,
  Divider,
  TextField,
} from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { useHospitals, useInventoryHistory } from '@/hooks/useApi'
import type { BloodType } from '@/types'
import { useTranslation } from 'react-i18next'

const BLOOD_TYPES: BloodType[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

function defaultDateRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 30)
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  }
}

interface SummaryCardProps {
  label: string
  value: string | number
  color?: string
}

function SummaryCard({ label, value, color }: SummaryCardProps) {
  return (
    <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography variant="h5" fontWeight="bold" sx={{ color: color ?? 'text.primary' }}>
        {value}
      </Typography>
    </Card>
  )
}

interface TooltipPayloadItem {
  name: string
  value: number
  color: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayloadItem[]
  label?: string
}

function HistoryTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null
  return (
    <Box
      sx={{
        background: 'rgba(255,255,255,0.97)',
        border: '1px solid #e0e0e0',
        borderRadius: 1,
        p: 1.5,
        boxShadow: 2,
        minWidth: 180,
      }}
    >
      <Typography variant="caption" fontWeight="bold" display="block" mb={0.5}>
        {label}
      </Typography>
      {payload.map(p => (
        <Typography key={p.name} variant="body2" sx={{ color: p.color }}>
          {p.name}: <strong>{p.value}</strong>
        </Typography>
      ))}
    </Box>
  )
}

export function HistoryPage() {
  const { t } = useTranslation()
  const range = defaultDateRange()
  const [hospitalId, setHospitalId] = useState('')
  const [bloodType, setBloodType] = useState<BloodType | ''>('')
  const [startDate, setStartDate] = useState(range.start)
  const [endDate, setEndDate] = useState(range.end)

  const { data: hospitals } = useHospitals()
  const { data: history, isLoading, isError } = useInventoryHistory(
    hospitalId,
    startDate,
    endDate,
    bloodType || undefined,
  )

  // Aggregate chart data by date (sum across blood types if no filter)
  const chartData = useMemo(() => {
    if (!history?.data) return []
    const byDate: Record<string, { date: string; consumed: number; wasted: number; net: number }> = {}
    for (const point of history.data) {
      if (!byDate[point.date]) {
        byDate[point.date] = { date: point.date, consumed: 0, wasted: 0, net: 0 }
      }
      byDate[point.date].consumed += point.units_consumed
      byDate[point.date].wasted += point.units_wasted
    }
    return Object.values(byDate)
      .sort((a, b) => a.date.localeCompare(b.date))
      .map(d => ({ ...d, net: d.consumed - d.wasted }))
  }, [history])

  const hasDeficits = chartData.some(d => d.net < 0)

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        {t('history.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        {t('history.subtitle')}
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>{t('common.hospital')}</InputLabel>
                <Select value={hospitalId} label={t('common.hospital')} onChange={e => setHospitalId(e.target.value)}>
                  {hospitals?.map(h => (
                    <MenuItem key={h.id} value={h.id}>{h.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={2}>
              <FormControl fullWidth>
                <InputLabel>{t('history.bloodTypeFilter')}</InputLabel>
                <Select
                  value={bloodType}
                  label={t('history.bloodTypeFilter')}
                  onChange={e => setBloodType(e.target.value as BloodType | '')}
                >
                  <MenuItem value="">{t('history.allTypes')}</MenuItem>
                  {BLOOD_TYPES.map(bt => (
                    <MenuItem key={bt} value={bt}>{bt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                type="date"
                label={t('history.startDate')}
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                type="date"
                label={t('history.endDate')}
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {!hospitalId && (
        <Alert severity="info">{t('common.selectHospital')}</Alert>
      )}

      {hospitalId && isLoading && <CircularProgress />}

      {hospitalId && isError && (
        <Alert severity="error">{t('history.loadError')}</Alert>
      )}

      {history && chartData.length > 0 && (
        <>
          {/* Summary cards */}
          <Grid container spacing={2} mb={3}>
            <Grid item xs={6} sm={3}>
              <SummaryCard
                label={t('history.totalConsumed')}
                value={history.summary.total_consumed}
                color="#1565c0"
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <SummaryCard
                label={t('history.totalWasted')}
                value={history.summary.total_wasted}
                color="#c62828"
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <SummaryCard
                label={t('history.wastageCost')}
                value={`€${history.summary.total_wastage_cost.toLocaleString('it-IT', { maximumFractionDigits: 0 })}`}
                color="#e65100"
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <SummaryCard
                label={t('history.deficitDays')}
                value={chartData.filter(d => d.net < 0).length}
                color={hasDeficits ? '#b71c1c' : 'success.main'}
              />
            </Grid>
          </Grid>

          {hasDeficits && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              {t('history.deficitAlert', { count: chartData.filter(d => d.net < 0).length })}
            </Alert>
          )}

          {/* Main chart */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('history.chartTitle')}
              </Typography>
              <ResponsiveContainer width="100%" height={380}>
                <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip content={<HistoryTooltip />} />
                  <Legend />
                  <ReferenceLine y={0} stroke="#666" />
                  <Bar dataKey="consumed" fill="#1565c0" name={t('history.consumed')} radius={[2, 2, 0, 0]} />
                  <Bar dataKey="wasted" fill="#c62828" name={t('history.wasted')} radius={[2, 2, 0, 0]} />
                  <Bar dataKey="net" fill="#2e7d32" name={t('history.net')} radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Breakdown by blood type */}
          {Object.keys(history.summary.by_blood_type).length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('history.byBloodType')}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  {Object.entries(history.summary.by_blood_type)
                    .sort((a, b) => b[1].consumed - a[1].consumed)
                    .map(([bt, data]) => (
                      <Grid item xs={12} sm={6} md={3} key={bt}>
                        <Card variant="outlined">
                          <CardContent sx={{ pb: '12px !important' }}>
                            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                              <Typography variant="h6" fontWeight="bold">{bt}</Typography>
                              {data.wasted > data.consumed * 0.15 && (
                                <Chip label={t('history.highWastage')} color="warning" size="small" />
                              )}
                            </Stack>
                            <Typography variant="body2" color="#1565c0">
                              {t('history.consumed')}: <strong>{data.consumed}</strong>
                            </Typography>
                            <Typography variant="body2" color="#c62828">
                              {t('history.wasted')}: <strong>{data.wasted}</strong>
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {t('history.wastageCost')}: €{data.wastage_cost.toLocaleString('it-IT', { maximumFractionDigits: 0 })}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                </Grid>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {history && chartData.length === 0 && hospitalId && (
        <Alert severity="info">{t('history.noData')}</Alert>
      )}
    </Box>
  )
}
