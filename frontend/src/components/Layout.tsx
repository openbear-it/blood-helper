import { type ReactNode, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Badge,
  Tooltip,
  Button,
  ButtonGroup,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import DashboardIcon from '@mui/icons-material/Dashboard'
import BloodtypeIcon from '@mui/icons-material/Bloodtype'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import HistoryIcon from '@mui/icons-material/History'
import VolunteerActivismIcon from '@mui/icons-material/VolunteerActivism'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { useAlertsWebSocket } from '@/hooks/useAlertsWebSocket'
import { useTranslation } from 'react-i18next'

const DRAWER_WIDTH = 240

const NAV_PATHS = [
  { key: 'dashboard', path: '/', icon: <DashboardIcon /> },
  { key: 'inventory', path: '/inventory', icon: <BloodtypeIcon /> },
  { key: 'forecasting', path: '/forecasting', icon: <TrendingUpIcon /> },
  { key: 'history', path: '/history', icon: <HistoryIcon /> },
  { key: 'campaigns', path: '/campaigns', icon: <VolunteerActivismIcon /> },
  { key: 'info', path: '/info', icon: <InfoOutlinedIcon /> },
]

const SUPPORTED_LANGS = [
  { code: 'it', label: '🇮🇹 IT' },
  { code: 'en', label: '🇬🇧 EN' },
]

export function Layout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { alerts } = useAlertsWebSocket()
  const { t, i18n } = useTranslation()
  const alertCount =
    (alerts?.critical_levels?.length ?? 0) + (alerts?.expiring_units?.length ?? 0)

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" color="primary" fontWeight="bold">
          🩸 blood-helper
        </Typography>
      </Toolbar>
      <List>
        {NAV_PATHS.map(item => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={t(`nav.${item.key}`)} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: theme => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            blood-helper Intelligence Platform
          </Typography>
          <ButtonGroup size="small" variant="outlined" sx={{ mr: 1 }}>
            {SUPPORTED_LANGS.map(lang => (
              <Button
                key={lang.code}
                onClick={() => i18n.changeLanguage(lang.code)}
                sx={{
                  color: 'white',
                  borderColor: 'rgba(255,255,255,0.5)',
                  fontWeight: i18n.language === lang.code ? 'bold' : 'normal',
                  bgcolor: i18n.language === lang.code ? 'rgba(255,255,255,0.15)' : 'transparent',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.25)', borderColor: 'white' },
                }}
              >
                {lang.label}
              </Button>
            ))}
          </ButtonGroup>
          {alertCount > 0 && (
            <Tooltip title={`${alertCount} active alerts`}>
              <Badge badgeContent={alertCount} color="warning">
                <WarningAmberIcon />
              </Badge>
            </Tooltip>
          )}
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          sx={{ display: { xs: 'block', sm: 'none' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{ display: { xs: 'none', sm: 'block' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` }, mt: 8 }}
      >
        {children}
      </Box>
    </Box>
  )
}
