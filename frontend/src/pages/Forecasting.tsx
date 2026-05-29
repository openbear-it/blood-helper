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
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  AreaChart,
  ResponsiveContainer,
} from 'recharts'
import { useHospitals, useForecasts, useRunForecast } from '@/hooks/useApi'
import type { BloodType, ForecastHorizon } from '@/types'

const BLOOD_TYPES: BloodType[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const HORIZONS: ForecastHorizon[] = ['daily', 'weekly', 'monthly']

export function ForecastingPage() {
  const [hospitalId, setHospitalId] = useState('')
  const [bloodType, setBloodType] = useState<BloodType>('O+')
  const [horizon, setHorizon] = useState<ForecastHorizon>('daily')

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
        Consumption Forecasting
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Hospital</InputLabel>
                <Select value={hospitalId} label="Hospital" onChange={e => setHospitalId(e.target.value)}>
                  {hospitals?.map(h => (
                    <MenuItem key={h.id} value={h.id}>{h.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Blood Type</InputLabel>
                <Select value={bloodType} label="Blood Type" onChange={e => setBloodType(e.target.value as BloodType)}>
                  {BLOOD_TYPES.map(bt => (
                    <MenuItem key={bt} value={bt}>{bt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Horizon</InputLabel>
                <Select value={horizon} label="Horizon" onChange={e => setHorizon(e.target.value as ForecastHorizon)}>
                  {HORIZONS.map(h => (
                    <MenuItem key={h} value={h}>{h.charAt(0).toUpperCase() + h.slice(1)}</MenuItem>
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
                {runMutation.isPending ? <CircularProgress size={20} /> : 'Run Forecast'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {runMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>Failed to run forecast. Please try again.</Alert>
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
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="upper"
                  fill="#ffccbc"
                  stroke="transparent"
                  name="Upper Bound"
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  fill="white"
                  stroke="transparent"
                  name="Lower Bound"
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#c62828"
                  strokeWidth={2}
                  dot={false}
                  name="Predicted Units"
                />
              </AreaChart>
            </ResponsiveContainer>
            {forecasts?.[0] && (
              <Typography variant="caption" color="textSecondary">
                Confidence: {(forecasts[0].confidence * 100).toFixed(0)}%
              </Typography>
            )}
          </CardContent>
        </Card>
      ) : hospitalId ? (
        <Alert severity="info">No forecast data available. Click "Run Forecast" to generate predictions.</Alert>
      ) : null}
    </Box>
  )
}
