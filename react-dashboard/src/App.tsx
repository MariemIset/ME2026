import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import DashboardLayout from './components/layout/DashboardLayout';
import Login from './pages/Login';
import CeoOverview from './pages/dashboards/CeoOverview';
import ChurnRisk from './pages/dashboards/ChurnRisk';
import LoyaltyEconomics from './pages/dashboards/LoyaltyEconomics';
import SatisfactionDrivers from './pages/dashboards/SatisfactionDrivers';
import MarketingLoyalty from './pages/dashboards/MarketingLoyalty';
import ProcessManagement from './pages/dashboards/ProcessManagement';
import ClientFeedback from './pages/ClientFeedback';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/feedback" element={<ClientFeedback />} />

          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Navigate to="/ceo-overview" replace />} />
            <Route path="/ceo-overview" element={<CeoOverview />} />
            <Route path="/churn-risk" element={<ChurnRisk />} />
            <Route path="/loyalty-economics" element={<LoyaltyEconomics />} />
            <Route path="/satisfaction-drivers" element={<SatisfactionDrivers />} />
            <Route path="/marketing-loyalty" element={<MarketingLoyalty />} />
            <Route path="/process-management" element={<ProcessManagement />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
