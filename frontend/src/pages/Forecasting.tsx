import { useState } from 'react'
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
  Button,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  ResponsiveContainer,
} from 'recharts'
import { useHospitals, useForecasts, useRunForecast } from '@/hooks/useApi'
import type { BloodType, ForecastHorizon } from '@/types'
import { useTranslation } from 'react-i18next'

const BLOOD_TYPES: BloodType[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const HORIZONS: ForecastHorizon[] = ['daily', 'weekly', 'monthly']

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

function ForecastTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null

  const predicted = payload.find(p => p.name === 'predicted')
  const upper = payload.find(p => p.name === 'upper')
  const lower = payload.find(p => p.name === 'lower')

  return (
    <Box
      sx={{
        background: 'rgba(255,255,255,0.97)',
        border: '1px solid #e0e0e0',
        borderRadius: 1,
        p: 1.5,
        boxShadow: 2,
        minWidth: 160,
      }}
    >
      <Typography variant="caption" display="block" fontWeight="bold" mb={0.5}>
        {label}
      </Typography>
      {predicted && (
        <Typography variant="body2" sx={{ color: '#c62828' }}>
          Previsto: <strong>{predicted.value}</strong>
        </Typography>
      )}
      {upper && lower && (
        <Typography variant="caption" color="text.secondary">
          Intervallo: {lower.value} – {upper.value}
        </Typography>
      )}
    </Box>
  )
}

export function ForecastingPage() {
  const [hospitalId, setHospitalId] = useState('')
  const [bloodType, setBloodType] = useState<BloodType>('O+')
  const [horizon, setHorizon] = useState<ForecastHorizon>('daily')
  const { t } = useTranslation()

  const { data: hospitals } = useHospitals()
  const { data: forecasts, isLoading } = useForecasts(hospitalId, bloodType, horizon)
  const runMutation = useRunForecast(hospitalId)

  const chartData = forecasts?.map(f => ({
    date: f.forecast_date,
    predicted: Number(f.predicted_units.toFixed(1)),
    lower: Number(f.lower_bound.toFixed(1)),
    upper: Number(f.upper_bound.toFixed(1)),
  })) ?? []

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        {t('forecasting.title')}
      </Typography>

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
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>{t('forecasting.bloodType')}</InputLabel>
                <Select value={bloodType} label={t('forecasting.bloodType')} onChange={e => setBloodType(e.target.value as BloodType)}>
                  {BLOOD_TYPES.map(bt => (
                    <MenuItem key={bt} value={bt}>{bt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>{t('forecasting.horizon')}</InputLabel>
                <Select value={horizon} label={t('forecasting.horizon')} onChange={e => setHorizon(e.target.value as ForecastHorizon)}>
                  {HORIZONS.map(h => (
                    <MenuItem key={h} value={h}>{t(`forecasting.horizons.${h}`)}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                variant="contained"
                fullWidth
                disabled={!hospitalId || runMutation.isPending}
                onClick={() => runMutation.mutate({ blood_type: bloodType, horizon })}
              >
                {runMutation.isPending ? <CircularProgress size={20} /> : t('forecasting.runForecast')}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {runMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>{t('forecasting.noData')}</Alert>
      )}

      {isLoading ? (
        <CircularProgress />
      ) : chartData.length > 0 ? (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Forecast: {bloodType} ({horizon}) — Model: {forecasts?.[0]?.model_name}
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip content={<ForecastTooltip />} />
                <Legend
                  formatter={(value: string) => {
                    if (value === 'predicted') return t('forecasting.predicted')
                    if (value === 'upper') return t('forecasting.confidence')
                    return null
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="upper"
                  fill="#ffccbc"
                  stroke="transparent"
                  name="upper"
                  legendType="none"
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  fill="white"
                  stroke="transparent"
                  name="lower"
                  legendType="none"
                  tooltipType="none"
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#c62828"
                  strokeWidth={2}
                  dot={false}
                  name="predicted"
                  activeDot={{ r: 5 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
            {forecasts?.[0] && (
              <Typography variant="caption" color="textSecondary">
                Confidence: {(forecasts[0].confidence * 100).toFixed(0)}%
              </Typography>
            )}
          </CardContent>
        </Card>
      ) : hospitalId ? (
        <Alert severity="info">{t('forecasting.noData')}</Alert>
      ) : null}
    </Box>
  )
}

