import { Grid, Card, CardContent, Typography, Chip, LinearProgress, Box } from '@mui/material'
import { useHospitals, useInventorySummary, useActiveCampaigns } from '@/hooks/useApi'
import { useAlertsWebSocket } from '@/hooks/useAlertsWebSocket'

const BLOOD_TYPE_COLORS: Record<string, string> = {
  'O+': '#e53935', 'O-': '#c62828',
  'A+': '#1e88e5', 'A-': '#1565c0',
  'B+': '#43a047', 'B-': '#2e7d32',
  'AB+': '#8e24aa', 'AB-': '#6a1b9a',
}

function HospitalInventoryCard({ hospitalId, hospitalName }: { hospitalId: string; hospitalName: string }) {
  const { data: summary } = useInventorySummary(hospitalId)

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
            ⚠ Critical: {summary.critical_types.join(', ')}
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

  const activeCampaigns = campaigns?.length ?? 0
  const criticalAlerts = alerts?.critical_levels?.length ?? 0
  const expiringAlerts = alerts?.expiring_units?.length ?? 0

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h3">{hospitals?.length ?? '—'}</Typography>
              <Typography variant="body1">Hospitals Monitored</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: criticalAlerts > 0 ? 'error.main' : 'success.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h3">{criticalAlerts}</Typography>
              <Typography variant="body1">Critical Alerts</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: expiringAlerts > 0 ? 'warning.main' : 'info.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h3">{expiringAlerts}</Typography>
              <Typography variant="body1">Expiring Units (3d)</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h5" gutterBottom>Inventory by Hospital</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {hospitals?.map(h => (
          <Grid item xs={12} md={6} key={h.id}>
            <HospitalInventoryCard hospitalId={h.id} hospitalName={h.name} />
          </Grid>
        ))}
      </Grid>

      {campaigns && campaigns.length > 0 && (
        <>
          <Typography variant="h5" gutterBottom>Active Donation Campaigns</Typography>
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
