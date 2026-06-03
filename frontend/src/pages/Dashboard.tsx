import { useState } from 'react'
import {
  Grid, Card, CardContent, Typography, Chip, LinearProgress, Box,
  Tooltip, ToggleButton, ToggleButtonGroup, Skeleton, Divider,
} from '@mui/material'
import { useHospitals, useInventorySummary, useActiveCampaigns, usePSI } from '@/hooks/useApi'
import { useAlertsWebSocket } from '@/hooks/useAlertsWebSocket'
import type { ScenarioMethod, PSIBloodTypeResult } from '@/types'
import { useTranslation } from 'react-i18next'

const BLOOD_TYPE_COLORS: Record<string, string> = {
  'O+': '#e53935', 'O-': '#c62828',
  'A+': '#1e88e5', 'A-': '#1565c0',
  'B+': '#43a047', 'B-': '#2e7d32',
  'AB+': '#8e24aa', 'AB-': '#6a1b9a',
}

function psiColor(psi: number): string {
  if (psi >= 1.5) return '#2e7d32'
  if (psi >= 1.0) return '#f57c00'
  return '#c62828'
}

function psiLabel(psi: number): string {
  if (psi === Infinity || psi > 99) return '∞'
  return psi.toFixed(2)
}

function PSIBar({ row }: { row: PSIBloodTypeResult }) {
  const { t } = useTranslation()
  const capped = Math.min(row.psi, 3)
  const pct = (capped / 3) * 100
  const color = psiColor(row.psi)
  return (
    <Tooltip
      title={
        <Box sx={{ fontSize: 12 }}>
          <div>{t('dashboard.stockNetValid')}: <b>{row.stock_net_valid}</b> u</div>
          <div>{t('dashboard.stockTotal')}: {row.stock_total} u</div>
          <div>{t('dashboard.atRisk')}: {row.at_risk_units} u</div>
          <div>{t('dashboard.expectedDemand')}: {row.expected_demand} u</div>
          <div>{t('dashboard.expectedInflows')}: {row.expected_inflows} u</div>
        </Box>
      }
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
        <Typography variant="caption" sx={{ width: 36, fontWeight: 'bold', color: BLOOD_TYPE_COLORS[row.blood_type] }}>
          {row.blood_type}
        </Typography>
        <Box sx={{ flex: 1, bgcolor: '#f5f5f5', borderRadius: 1, height: 10, overflow: 'hidden' }}>
          <Box sx={{ width: `${pct}%`, bgcolor: color, height: '100%', transition: 'width 0.4s' }} />
        </Box>
        <Typography variant="caption" sx={{ width: 36, fontWeight: 'bold', color }}>
          {psiLabel(row.psi)}
        </Typography>
      </Box>
    </Tooltip>
  )
}

function PSICard({ hospitalId, hospitalName }: { hospitalId: string; hospitalName: string }) {
  const [horizon, setHorizon] = useState(7)
  const [percentile, setPercentile] = useState<50 | 95>(95)
  const [method, setMethod] = useState<ScenarioMethod>('static')
  const { t } = useTranslation()

  const { data, isLoading } = usePSI(hospitalId, { horizon_days: horizon, percentile, method })

  const overallColor = data ? psiColor(data.overall_psi) : '#9e9e9e'

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold">{hospitalName}</Typography>
          {data && (
            <Chip
              label={`PSI ${psiLabel(data.overall_psi)}`}
              size="small"
              sx={{ bgcolor: overallColor, color: 'white', fontWeight: 'bold' }}
            />
          )}
        </Box>

        {/* Controls */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1.5 }}>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={horizon}
            onChange={(_, v) => v && setHorizon(v)}
          >
            <ToggleButton value={3}>3d</ToggleButton>
            <ToggleButton value={7}>7d</ToggleButton>
            <ToggleButton value={14}>14d</ToggleButton>
          </ToggleButtonGroup>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={percentile}
            onChange={(_, v) => v && setPercentile(v)}
          >
            <ToggleButton value={50}>p50</ToggleButton>
            <ToggleButton value={95}>p95</ToggleButton>
          </ToggleButtonGroup>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={method}
            onChange={(_, v) => v && setMethod(v)}
          >
            <ToggleButton value="static">{t('psi.static')}</ToggleButton>
            <ToggleButton value="ewma">{t('psi.ewma')}</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Divider sx={{ mb: 1 }} />

        {isLoading && <Skeleton variant="rectangular" height={120} />}

        {data && (
          <Box>
            {data.by_blood_type.map(row => (
              <PSIBar key={row.blood_type} row={row} />
            ))}
            {data.critical_types.length > 0 && (
              <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                ⚠ {t('dashboard.psiCritical', { types: data.critical_types.join(', ') })}
              </Typography>
            )}
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              {t('dashboard.psiFormula', { days: horizon, percentile })}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

function HospitalInventoryCard({ hospitalId, hospitalName }: { hospitalId: string; hospitalName: string }) {
  const { data: summary } = useInventorySummary(hospitalId)
  const { t } = useTranslation()

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>{hospitalName}</Typography>
        {summary ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {Object.entries(summary.blood_types).map(([bt, data]) => (
              <Chip
                key={bt}
                label={`${bt}: ${data.available}`}
                size="small"
                sx={{
                  backgroundColor: BLOOD_TYPE_COLORS[bt] ?? '#757575',
                  color: 'white',
                  fontWeight: 'bold',
                }}
              />
            ))}
          </Box>
        ) : (
          <LinearProgress />
        )}
        {summary && summary.critical_types.length > 0 && (
          <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
            ⚠ {t('dashboard.critical')}: {summary.critical_types.join(', ')}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

export function Dashboard() {
  const { data: hospitals } = useHospitals()
  const { data: campaigns } = useActiveCampaigns()
  const { alerts } = useAlertsWebSocket()
  const { t } = useTranslation()

  const activeCampaigns = campaigns?.length ?? 0
  const criticalAlerts = alerts?.critical_levels?.length ?? 0
  const expiringAlerts = alerts?.expiring_units?.length ?? 0

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        {t('dashboard.title')}
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h3">{hospitals?.length ?? '—'}</Typography>
              <Typography variant="body1">{t('dashboard.hospitalsMonitored')}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: criticalAlerts > 0 ? 'error.main' : 'success.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h3">{criticalAlerts}</Typography>
              <Typography variant="body1">{t('dashboard.criticalAlerts')}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: expiringAlerts > 0 ? 'warning.main' : 'info.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h3">{expiringAlerts}</Typography>
              <Typography variant="body1">{t('dashboard.expiringUnits')}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'secondary.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h3">{activeCampaigns}</Typography>
              <Typography variant="body1">{t('dashboard.activeCampaigns')}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h5" gutterBottom>{t('dashboard.inventoryByHospital')}</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {hospitals?.map(h => (
          <Grid item xs={12} md={6} key={h.id}>
            <HospitalInventoryCard hospitalId={h.id} hospitalName={h.name} />
          </Grid>
        ))}
      </Grid>

      <Typography variant="h5" gutterBottom>
        {t('dashboard.psiTitle')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('dashboard.psiLegend')}
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {hospitals?.map(h => (
          <Grid item xs={12} md={6} key={h.id}>
            <PSICard hospitalId={h.id} hospitalName={h.name} />
          </Grid>
        ))}
      </Grid>

      {campaigns && campaigns.length > 0 && (
        <>
          <Typography variant="h5" gutterBottom>{t('dashboard.activeDonationCampaigns')}</Typography>
          <Grid container spacing={2}>
            {campaigns.map(c => (
              <Grid item xs={12} md={6} key={c.id}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight="bold">{c.title}</Typography>
                    <LinearProgress
                      variant="determinate"
                      value={c.progress_percentage}
                      sx={{ my: 1 }}
                      color={c.progress_percentage >= 80 ? 'success' : 'primary'}
                    />
                    <Typography variant="caption">
                      {c.collected_units} / {c.target_units} units ({c.progress_percentage.toFixed(1)}%)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Box>
  )
}
