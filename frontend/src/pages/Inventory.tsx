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
  Chip,
  LinearProgress,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
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
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { useHospitals, useInventorySummary, useWastageAnalysis, useAddBloodUnits } from '@/hooks/useApi'
import type { BloodType } from '@/types'
import { useTranslation } from 'react-i18next'

const STATUS_COLORS = {
  adequate: '#4caf50',
  low: '#ff9800',
  critical: '#f44336',
  surplus: '#2196f3',
}

const PIE_COLORS = ['#c62828', '#1565c0', '#2e7d32', '#6a1b9a', '#e65100', '#00838f', '#37474f', '#ad1457']

export function InventoryPage() {
  const [hospitalId, setHospitalId] = useState('')
  const [addOpen, setAddOpen] = useState(false)
  const [addForm, setAddForm] = useState({ blood_type: 'O+' as BloodType, units_available: 10, expiry_date: '' })
  const { t } = useTranslation()

  const { data: hospitals } = useHospitals()
  const { data: summary, isLoading } = useInventorySummary(hospitalId)
  const today = new Date()
  const monthAgo = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate())
  const { data: wastage } = useWastageAnalysis(
    hospitalId,
    monthAgo.toISOString().split('T')[0],
    today.toISOString().split('T')[0],
  )
  const addMutation = useAddBloodUnits(hospitalId)

  const inventoryBarData = summary
    ? Object.entries(summary.blood_types).map(([bt, data]) => ({
        blood_type: bt,
        available: data.available,
        reserved: data.reserved,
        expiring: data.expiring_soon,
      }))
    : []

  const wastageByType = wastage
    ? Object.entries(wastage.by_blood_type).map(([bt, data], i) => ({
        name: bt,
        value: data.units,
        fill: PIE_COLORS[i % PIE_COLORS.length],
      }))
    : []

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">{t('inventory.title')}</Typography>

      <Grid container spacing={2} sx={{ mb: 3 }} alignItems="center">
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth>
            <InputLabel>{t('common.selectHospital')}</InputLabel>
            <Select value={hospitalId} label={t('common.selectHospital')} onChange={e => setHospitalId(e.target.value)}>
              {hospitals?.map(h => (
                <MenuItem key={h.id} value={h.id}>{h.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        {hospitalId && (
          <Grid item>
            <Button variant="contained" onClick={() => setAddOpen(true)}>{t('inventory.addUnits')}</Button>
          </Grid>
        )}
      </Grid>

      {isLoading && <LinearProgress />}

      {summary && (
        <>
          {summary.critical_types.length > 0 && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {t('inventory.criticalInventory', { types: summary.critical_types.join(', ') })}
            </Alert>
          )}

          <Grid container spacing={2} sx={{ mb: 2 }}>
            {Object.entries(summary.blood_types).map(([bt, data]) => {
              const status = data.available === 0 ? 'critical' : data.available < 5 ? 'low' : data.available > 50 ? 'surplus' : 'adequate'
              return (
                <Grid item xs={6} sm={3} key={bt}>
                  <Card sx={{ borderLeft: `4px solid ${STATUS_COLORS[status]}` }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography variant="h5" fontWeight="bold">{bt}</Typography>
                      <Typography variant="h4" color={STATUS_COLORS[status]}>{data.available}</Typography>
                      <Typography variant="caption">{t('common.units')}</Typography>
                      <br />
                      <Chip label={status} size="small" sx={{ mt: 0.5, backgroundColor: STATUS_COLORS[status], color: 'white' }} />
                    </CardContent>
                  </Card>
                </Grid>
              )
            })}
          </Grid>

          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6">{t('inventory.inventoryByType')}</Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={inventoryBarData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="blood_type" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="available" fill="#1565c0" name={t('inventory.available')} />
                      <Bar dataKey="reserved" fill="#ff9800" name={t('inventory.reserved')} />
                      <Bar dataKey="expiring" fill="#f44336" name={t('inventory.expiringSoon')} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            {wastage && wastageByType.length > 0 && (
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{t('inventory.wastageByType')}</Typography>
                    <Typography variant="h5" color="error">
                      {wastage.total_units_wasted} units
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      €{wastage.total_estimated_cost.toFixed(2)} estimated cost
                    </Typography>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie data={wastageByType} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}>
                          {wastageByType.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        </>
      )}

      <Dialog open={addOpen} onClose={() => setAddOpen(false)}>
        <DialogTitle>{t('inventory.addUnitsTitle')}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <FormControl>
            <InputLabel>{t('inventory.bloodType')}</InputLabel>
            <Select
              value={addForm.blood_type}
              label={t('inventory.bloodType')}
              onChange={e => setAddForm(f => ({ ...f, blood_type: e.target.value as BloodType }))}
            >
              {(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as BloodType[]).map(bt => (
                <MenuItem key={bt} value={bt}>{bt}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label={t('inventory.unitsCount')}
            type="number"
            value={addForm.units_available}
            onChange={e => setAddForm(f => ({ ...f, units_available: Number(e.target.value) }))}
          />
          <TextField
            label={t('inventory.expiryDate')}
            type="date"
            InputLabelProps={{ shrink: true }}
            value={addForm.expiry_date}
            onChange={e => setAddForm(f => ({ ...f, expiry_date: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>{t('common.cancel')}</Button>
          <Button
            variant="contained"
            disabled={addMutation.isPending || !addForm.expiry_date}
            onClick={() => {
              addMutation.mutate(addForm, { onSuccess: () => setAddOpen(false) })
            }}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
