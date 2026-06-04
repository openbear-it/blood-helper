import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
} from '@mui/material'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import FunctionsIcon from '@mui/icons-material/Functions'
import MemoryIcon from '@mui/icons-material/Memory'
import BarChartIcon from '@mui/icons-material/BarChart'
import BuildIcon from '@mui/icons-material/Build'
import { useTranslation } from 'react-i18next'

const BLOOD_TYPE_COLORS = ['#c62828', '#1565c0', '#2e7d32', '#6a1b9a', '#e65100', '#00838f', '#37474f', '#ad1457']

function SectionCard({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode
  title: string
  children: React.ReactNode
}) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Box sx={{ color: 'primary.main', display: 'flex' }}>{icon}</Box>
          <Typography variant="h6" fontWeight="bold">
            {title}
          </Typography>
        </Box>
        {children}
      </CardContent>
    </Card>
  )
}

export function InfoPage() {
  const { t } = useTranslation()

  const features = t('info.features', { returnObjects: true }) as string[]
  const architectureItems = t('info.architectureItems', { returnObjects: true }) as { label: string; value: string }[]
  const mlModels = t('info.mlModels', { returnObjects: true }) as { name: string; description: string }[]
  const psiComponents = t('info.psiComponents', { returnObjects: true }) as { label: string; value: string }[]
  const psiThresholds = t('info.psiThresholds', { returnObjects: true }) as { label: string; color: string; meaning: string }[]

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          🩸 {t('info.title')}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {t('info.subtitle')}
        </Typography>
        <Box sx={{ mt: 1 }}>
          <Chip label={`${t('info.versionLabel')} ${t('info.version')}`} size="small" color="primary" variant="outlined" />
        </Box>
      </Box>

      {/* Overview */}
      <SectionCard icon={<BarChartIcon />} title={t('info.overviewTitle')}>
        <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
          {t('info.overviewText')}
        </Typography>

        <Typography variant="subtitle2" fontWeight="bold" sx={{ mt: 2, mb: 1 }}>
          {t('info.featuresTitle')}
        </Typography>
        <List dense disablePadding>
          {features.map((f, i) => (
            <ListItem key={i} disablePadding sx={{ py: 0.25 }}>
              <ListItemIcon sx={{ minWidth: 32 }}>
                <CheckCircleOutlineIcon fontSize="small" color="success" />
              </ListItemIcon>
              <ListItemText primary={f} primaryTypographyProps={{ variant: 'body2' }} />
            </ListItem>
          ))}
        </List>
      </SectionCard>

      {/* PSI Algorithm */}
      <SectionCard icon={<FunctionsIcon />} title={t('info.psiTitle')}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('info.psiDescription')}
        </Typography>

        <Paper
          variant="outlined"
          sx={{
            p: 2,
            mb: 3,
            bgcolor: 'grey.50',
            fontFamily: 'monospace',
            textAlign: 'center',
            fontSize: '1.05rem',
            fontWeight: 'bold',
            letterSpacing: 0.5,
          }}
        >
          {t('info.psiFormula')}
        </Paper>

        <Grid container spacing={2} sx={{ mb: 3 }}>
          {psiComponents.map((c, i) => (
            <Grid item xs={12} sm={6} key={i}>
              <Box sx={{ p: 1.5, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold" color="primary.main" display="block">
                  {c.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {c.value}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>

        <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
          Thresholds
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {psiThresholds.map((th, i) => (
            <Paper
              key={i}
              variant="outlined"
              sx={{ px: 2, py: 1, borderLeft: `4px solid ${th.color}`, flex: 1, minWidth: 160 }}
            >
              <Typography variant="caption" fontWeight="bold" sx={{ color: th.color }} display="block">
                {th.label}
              </Typography>
              <Typography variant="body2">{th.meaning}</Typography>
            </Paper>
          ))}
        </Box>
      </SectionCard>

      {/* ML Models */}
      <SectionCard icon={<MemoryIcon />} title={t('info.mlTitle')}>
        <Grid container spacing={2}>
          {mlModels.map((m, i) => (
            <Grid item xs={12} md={4} key={i}>
              <Box
                sx={{
                  p: 2,
                  height: '100%',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  borderTop: `3px solid ${BLOOD_TYPE_COLORS[i % BLOOD_TYPE_COLORS.length]}`,
                }}
              >
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  {m.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                  {m.description}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </SectionCard>

      {/* Architecture */}
      <SectionCard icon={<BuildIcon />} title={t('info.architectureTitle')}>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableBody>
              {architectureItems.map((item, i) => (
                <TableRow key={i} sx={{ '&:last-child td': { border: 0 } }}>
                  <TableCell
                    sx={{
                      width: 160,
                      fontWeight: 'bold',
                      color: 'primary.main',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {item.label}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{item.value}</Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Divider sx={{ my: 2 }} />

        {/* Blood type palette */}
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          Supported blood types:
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
          {['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'].map((bt, i) => (
            <Chip
              key={bt}
              label={bt}
              size="small"
              sx={{ bgcolor: BLOOD_TYPE_COLORS[i], color: 'white', fontWeight: 'bold' }}
            />
          ))}
        </Box>
      </SectionCard>
    </Box>
  )
}
