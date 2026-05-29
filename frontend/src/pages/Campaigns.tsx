import { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  OutlinedInput,
} from '@mui/material'
import { useActiveCampaigns, useHospitals, useDonateToMutation } from '@/hooks/useApi'
import { campaignApi } from '@/services/api'
import { useQueryClient } from '@tanstack/react-query'
import type { BloodType, Campaign } from '@/types'

const STATUS_COLOR: Record<string, 'success' | 'primary' | 'default' | 'error'> = {
  active: 'success',
  draft: 'primary',
  completed: 'default',
  cancelled: 'error',
}

function CampaignCard({ campaign }: { campaign: Campaign }) {
  const [donateOpen, setDonateOpen] = useState(false)
  const [units, setUnits] = useState(1)
  const donateMutation = useDonateToMutation(campaign.id)
  const qc = useQueryClient()

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <Typography variant="h6">{campaign.title}</Typography>
          <Chip label={campaign.status} color={STATUS_COLOR[campaign.status] ?? 'default'} size="small" />
        </Box>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
          {campaign.description}
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
          {campaign.target_blood_types.map(bt => (
            <Chip key={bt} label={bt} size="small" color="primary" variant="outlined" />
          ))}
        </Box>
        <LinearProgress
          variant="determinate"
          value={campaign.progress_percentage}
          sx={{ my: 1 }}
          color={campaign.progress_percentage >= 80 ? 'success' : 'primary'}
        />
        <Typography variant="caption">
          {campaign.collected_units} / {campaign.target_units} units ({campaign.progress_percentage.toFixed(1)}%)
        </Typography>
        <Typography variant="caption" display="block" color="textSecondary">
          {campaign.start_date} → {campaign.end_date}
        </Typography>
        {campaign.status === 'active' && (
          <Button size="small" variant="contained" sx={{ mt: 1 }} onClick={() => setDonateOpen(true)}>
            Donate
          </Button>
        )}
        {campaign.status === 'draft' && (
          <Button
            size="small"
            variant="outlined"
            color="success"
            sx={{ mt: 1, ml: 1 }}
            onClick={() => {
              campaignApi.activate(campaign.id).then(() => qc.invalidateQueries({ queryKey: ['campaigns'] }))
            }}
          >
            Activate
          </Button>
        )}
      </CardContent>

      <Dialog open={donateOpen} onClose={() => setDonateOpen(false)}>
        <DialogTitle>Record Donation</DialogTitle>
        <DialogContent>
          <TextField
            label="Units"
            type="number"
            value={units}
            onChange={e => setUnits(Number(e.target.value))}
            inputProps={{ min: 1 }}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDonateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={donateMutation.isPending}
            onClick={() => donateMutation.mutate(units, { onSuccess: () => setDonateOpen(false) })}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  )
}

export function CampaignsPage() {
  const { data: campaigns, isLoading } = useActiveCampaigns()
  const { data: hospitals } = useHospitals()
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({
    hospitalId: '',
    title: '',
    description: '',
    target_blood_types: [] as BloodType[],
    target_units: 100,
    start_date: '',
    end_date: '',
  })
  const qc = useQueryClient()

  const handleCreate = async () => {
    await campaignApi.create(form.hospitalId, {
      title: form.title,
      description: form.description,
      target_blood_types: form.target_blood_types,
      target_units: form.target_units,
      start_date: form.start_date,
      end_date: form.end_date,
    })
    qc.invalidateQueries({ queryKey: ['campaigns'] })
    setCreateOpen(false)
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" fontWeight="bold">Donation Campaigns</Typography>
        <Button variant="contained" onClick={() => setCreateOpen(true)}>+ New Campaign</Button>
      </Box>

      {isLoading ? (
        <LinearProgress />
      ) : (
        <Grid container spacing={2}>
          {campaigns?.map(c => (
            <Grid item xs={12} md={6} key={c.id}>
              <CampaignCard campaign={c} />
            </Grid>
          ))}
          {!campaigns?.length && (
            <Grid item xs={12}>
              <Typography color="textSecondary">No active campaigns.</Typography>
            </Grid>
          )}
        </Grid>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Campaign</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <FormControl>
            <InputLabel>Hospital</InputLabel>
            <Select
              value={form.hospitalId}
              label="Hospital"
              onChange={e => setForm(f => ({ ...f, hospitalId: e.target.value }))}
            >
              {hospitals?.map(h => <MenuItem key={h.id} value={h.id}>{h.name}</MenuItem>)}
            </Select>
          </FormControl>
          <TextField label="Title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
          <TextField
            label="Description"
            multiline
            rows={2}
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
          <FormControl>
            <InputLabel>Target Blood Types</InputLabel>
            <Select
              multiple
              value={form.target_blood_types}
              onChange={e => setForm(f => ({ ...f, target_blood_types: e.target.value as BloodType[] }))}
              input={<OutlinedInput label="Target Blood Types" />}
              renderValue={selected => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as BloodType[]).map(v => <Chip key={v} label={v} size="small" />)}
                </Box>
              )}
            >
              {(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as BloodType[]).map(bt => (
                <MenuItem key={bt} value={bt}>{bt}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Target Units"
            type="number"
            value={form.target_units}
            onChange={e => setForm(f => ({ ...f, target_units: Number(e.target.value) }))}
          />
          <TextField
            label="Start Date"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={form.start_date}
            onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
          />
          <TextField
            label="End Date"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={form.end_date}
            onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!form.hospitalId || !form.title || !form.start_date || !form.end_date}
            onClick={handleCreate}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
