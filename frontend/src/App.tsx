import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { InventoryPage } from '@/pages/Inventory'
import { ForecastingPage } from '@/pages/Forecasting'
import { CampaignsPage } from '@/pages/Campaigns'
import { InfoPage } from '@/pages/Info'
import { Providers } from '@/providers'

function App() {
  return (
    <Providers>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/forecasting" element={<ForecastingPage />} />
            <Route path="/campaigns" element={<CampaignsPage />} />
            <Route path="/info" element={<InfoPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </Providers>
  )
}

export default App
